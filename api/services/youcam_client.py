"""
YouCam (Perfect Corp) Skin Analysis client — v2 API.

Confirmed live against the real API (not just docs) on 2026-08-16:
  - auth: `Authorization: Bearer $YOUCAM_API_KEY`
  - base server: https://yce-api-01.makeupar.com
  - every response is enveloped as {"status": 200, "data": {...}} — the
    actual payload is one level deeper than the top-level JSON body.
  - File API: POST /s2s/v2.0/file, body
    {"files": [{"content_type": ..., "file_name": ..., "file_size": ...}]}
    (file_name and file_size are REQUIRED — YouCam 400s without them).
    Response: data.files[0].file_id, data.files[0].requests[0] is the
    {method, url, headers} to PUT the raw bytes to (a pre-signed S3 URL —
    the returned headers, including Content-Length, must be sent verbatim
    or the signature check fails).
  - Task creation: POST /s2s/v2.0/task/skin-analysis, body
    {"src_file_id": ..., "dst_actions": [...]} (NOT "file_id"/"actions" —
    confirmed via the API's own 400 error naming the required fields).
    Response: data.task_id.
  - Task polling: GET /s2s/v2.0/task/skin-analysis/{task_id}.
    Response: data.task_status in {"running", "success", "error"}; on
    error, data.error has a message; on success, data.results holds the
    scores (exact internal shape still unconfirmed — see note below).
  - Concern names verified valid via live probing: wrinkle, pore, acne,
    redness, oiliness, radiance, texture, firmness, eye_bag, moisture,
    age_spot, droopy_upper_eyelid, droopy_lower_eyelid. NOT valid (rejected
    by the API): dryness, dark_spot, dark_circle, hydration, spot, sagging,
    melanin, hemoglobin, shine — despite being named in the original plan
    doc / earlier guesses. "dryness" is actually called "moisture" and
    "dark_spot" is actually called "age_spot".

Also confirmed via a real successful task: `data.results` is
{"url": "<pre-signed S3 zip url>"} — NOT inline scores. The zip contains
skinanalysisResult/score_info.json ({metric: {"raw_score", "ui_score",
"output_mask_name"}, "all": {"score": ...}, "skin_age": int,
"resize_image": {...}}) plus one annotated output PNG per metric. See
_fetch_results for the download/parse/image-extraction logic.
"""

import asyncio
import base64
import json
import os
import time
import uuid
import zipfile
from io import BytesIO

import httpx
from PIL import Image
from pydantic import BaseModel

from utils.file import return_file_contents

YOUCAM_API_BASE = os.getenv("YOUCAM_API_BASE", "https://yce-api-01.makeupar.com")
YOUCAM_API_KEY = os.getenv("YOUCAM_API_KEY")
YOUCAM_TIER = os.getenv("YOUCAM_TIER", "sd")  # "sd" | "hd"
YOUCAM_MOCK_MODE = os.getenv("YOUCAM_MOCK_MODE", "false").lower() == "true"
YOUCAM_MAX_UNITS_PER_SESSION = int(os.getenv("YOUCAM_MAX_UNITS_PER_SESSION", "50"))
MOCK_FIXTURE_PATH = os.path.join("tests", "fixtures", "skin_analysis_response.json")

if not YOUCAM_MOCK_MODE and not YOUCAM_API_KEY:
    raise EnvironmentError("YOUCAM_API_KEY must be set unless YOUCAM_MOCK_MODE=true.")

# Image spec (plan §2): long side <=4096, short side >=1080 for HD specifically.
# The SD-tier minimum was never confirmed against real docs (JS-rendered
# reference pages) — rather than guess a number and block valid SD uploads,
# the floor is only enforced for HD; SD relies on YouCam's own task response
# to signal an actually-too-small image, which is a more reliable source
# than a guessed constant.
MAX_LONG_SIDE = 4096
MIN_SHORT_SIDE_HD = 1080


class SkinMetric(BaseModel):
    name: str
    raw_score: float
    normalised: float  # 0-1, higher = more severe
    band: str  # "clear" | "mild" | "moderate" | "significant"
    band_distance: float  # 0-1, distance from nearest band boundary
    output_image: str | None = None  # data: URI of YouCam's annotated output mask for this metric, if available


class SkinAnalysisResult(BaseModel):
    metrics: list[SkinMetric]
    skin_age: int | None = None  # score_info.json "skin_age"
    overall_score: float | None = None  # score_info.json "all.score", 0-100, higher = healthier
    file_id: str
    task_id: str
    raw_payload: dict


# --- per-metric normalisation config ---------------------------------------
# raw_range: (min, max) — confirmed 0-100 from a real successful response.
# polarity: "higher_is_worse" (severity score) or "higher_is_better" (quality/health score).
#
# CONFIRMED via a real completed task (2026-08-16): every metric here is a
# 0-100 "ui_score" (not "raw_score" — the real payload has both; ui_score is
# what YouCam's own product surfaces to end users, so it's the one used for
# consistency with the source product). All are higher_is_better: the
# payload includes an "all": {"score": ...} composite that is a plain
# average across every per-metric score, which only makes sense if they all
# share one "higher = healthier" scale — you wouldn't average severity
# scores together and present it as a single "skin score" the way YouCam's
# own product does.
METRIC_CONFIG = {
    "moisture": {"raw_range": (0, 100), "polarity": "higher_is_better"},
    "wrinkle": {"raw_range": (0, 100), "polarity": "higher_is_better"},
    "redness": {"raw_range": (0, 100), "polarity": "higher_is_better"},
    "age_spot": {"raw_range": (0, 100), "polarity": "higher_is_better"},
    "acne": {"raw_range": (0, 100), "polarity": "higher_is_better"},
    "pore": {"raw_range": (0, 100), "polarity": "higher_is_better"},
    # Same verified skin-analysis task, extra concerns (names verified valid via
    # live probing — see module docstring). Same ui_score scale and polarity.
    "oiliness": {"raw_range": (0, 100), "polarity": "higher_is_better"},
    "radiance": {"raw_range": (0, 100), "polarity": "higher_is_better"},
    "texture": {"raw_range": (0, 100), "polarity": "higher_is_better"},
    "firmness": {"raw_range": (0, 100), "polarity": "higher_is_better"},
    "eye_bag": {"raw_range": (0, 100), "polarity": "higher_is_better"},
}

BAND_BOUNDARIES = [
    ("clear", 0.0, 0.25),
    ("mild", 0.25, 0.5),
    ("moderate", 0.5, 0.75),
    ("significant", 0.75, 1.0),
]


def _normalise(metric_name: str, raw_score: float) -> float:
    config = METRIC_CONFIG[metric_name]
    lo, hi = config["raw_range"]
    span = hi - lo if hi != lo else 1.0
    value = (raw_score - lo) / span
    value = max(0.0, min(1.0, value))
    if config["polarity"] == "higher_is_better":
        value = 1.0 - value
    return value


def _band_for(normalised: float) -> tuple[str, float]:
    for band, lo, hi in BAND_BOUNDARIES:
        if lo <= normalised <= hi:
            distance = min(abs(normalised - lo), abs(hi - normalised))
            return band, round(distance, 3)
    return "significant", 0.0


def _extract_scores(results) -> dict:
    """Fallback for inline results shapes (e.g. the mock fixture). The real
    API does NOT return inline scores here — see _fetch_scores below — but
    this stays as a defensive fallback and fails loudly rather than
    silently misparsing if a shape shows up that isn't handled."""
    if isinstance(results, dict):
        if all(isinstance(v, (int, float)) for v in results.values()):
            return results  # {metric_name: score, ...}
        if all(isinstance(v, dict) for v in results.values()):
            return {k: v.get("ui_score", v.get("score", v.get("value"))) for k, v in results.items()}
    if isinstance(results, list):
        scores = {}
        for item in results:
            if isinstance(item, dict):
                name = item.get("action") or item.get("name")
                score = item.get("score", item.get("value"))
                if name is not None and score is not None:
                    scores[name] = score
        if scores:
            return scores
    raise ValueError(f"Unrecognised YouCam results shape, update _extract_scores: {results!r}")


def _extract_summary(payload: dict) -> tuple[int | None, float | None]:
    """skin_age and the composite all.score, present alongside per-metric
    entries in score_info.json (and in the mock fixture)."""
    skin_age = payload.get("skin_age")
    overall = (payload.get("all") or {}).get("score") if isinstance(payload.get("all"), dict) else None
    return (int(skin_age) if isinstance(skin_age, (int, float)) else None,
            round(float(overall), 1) if isinstance(overall, (int, float)) else None)


async def _fetch_results(client: httpx.AsyncClient, results) -> tuple[dict, dict, dict]:
    """CONFIRMED (2026-08-16, real successful task): a completed task's
    `results` field is {"url": "<pre-signed S3 zip url>"}, NOT inline
    scores. The zip contains skinanalysisResult/score_info.json with
    per-metric {"raw_score", "ui_score", "output_mask_name"} entries (the
    named PNG is YouCam's own annotated visualisation for that metric, in
    the same zip), plus non-metric keys ("all", "skin_age", "resize_image")
    that get skipped here since they don't have a "ui_score" field.
    ui_score (not raw_score) is used — see METRIC_CONFIG comment for why.

    Returns (scores, output_images, score_info) where output_images maps
    metric name -> a data: URI of that metric's annotated PNG, for metrics
    whose mask was present in the zip, and score_info is the raw file (for
    skin_age / all.score)."""
    if isinstance(results, dict) and "url" in results:
        resp = await client.get(results["url"])
        resp.raise_for_status()
        with zipfile.ZipFile(BytesIO(resp.content)) as zf:
            score_file = next((n for n in zf.namelist() if n.endswith("score_info.json")), None)
            if not score_file:
                raise ValueError(f"No score_info.json in YouCam results zip: {zf.namelist()!r}")
            score_info = json.loads(zf.read(score_file))

            base_dir = score_file.rsplit("/", 1)[0] + "/" if "/" in score_file else ""
            scores = {}
            output_images = {}
            for name, value in score_info.items():
                if not (isinstance(value, dict) and "ui_score" in value):
                    continue
                scores[name] = value["ui_score"]
                mask_name = value.get("output_mask_name")
                mask_path = base_dir + mask_name if mask_name else None
                if mask_path and mask_path in zf.namelist():
                    mime = "image/png" if mask_path.lower().endswith(".png") else "image/jpeg"
                    encoded = base64.b64encode(zf.read(mask_path)).decode("ascii")
                    output_images[name] = f"data:{mime};base64,{encoded}"
        return scores, output_images, score_info
    return _extract_scores(results), {}, {}


def _to_skin_metrics(raw_scores: dict, output_images: dict | None = None) -> list[SkinMetric]:
    output_images = output_images or {}
    metrics = []
    for name, raw_score in raw_scores.items():
        if name not in METRIC_CONFIG:
            continue
        normalised = _normalise(name, raw_score)
        band, band_distance = _band_for(normalised)
        metrics.append(
            SkinMetric(
                name=name,
                raw_score=raw_score,
                normalised=round(normalised, 3),
                band=band,
                band_distance=band_distance,
                output_image=output_images.get(name),
            )
        )
    return metrics


def _validate_and_resize(image_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(image_bytes))
    width, height = img.size
    long_side, short_side = max(width, height), min(width, height)

    if YOUCAM_TIER == "hd" and short_side < MIN_SHORT_SIDE_HD:
        # Can't be fixed by resizing — upscaling can't manufacture real
        # resolution, so reject rather than let the YouCam API fail later.
        raise ValueError(
            f"Image short side {short_side}px is below the {MIN_SHORT_SIDE_HD}px minimum required for HD skin analysis."
        )

    if long_side <= MAX_LONG_SIDE:
        return image_bytes

    scale = MAX_LONG_SIDE / long_side
    img = img.resize((max(1, int(width * scale)), max(1, int(height * scale))))
    buf = BytesIO()
    img.save(buf, format=img.format or "JPEG")
    return buf.getvalue()


async def _with_retry(request_fn, attempts: int = 3, backoff_s: float = 1.0) -> httpx.Response:
    """Retries transient connection/timeout errors (seen in practice right
    after a Docker network stack restart) with short backoff. Does NOT
    retry on HTTP error status codes — those are real API responses, not
    transient failures, and raise_for_status() inside request_fn surfaces
    them immediately."""
    last_exc: Exception = RuntimeError("_with_retry called with attempts <= 0")
    for attempt in range(attempts):
        try:
            return await request_fn()
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            last_exc = e
            if attempt < attempts - 1:
                await asyncio.sleep(backoff_s * (attempt + 1))
    raise last_exc


async def _request_upload_url(client: httpx.AsyncClient, image_bytes: bytes) -> tuple[str, dict]:
    async def _do():
        resp = await client.post(
            f"{YOUCAM_API_BASE}/s2s/v2.0/file",
            json={"files": [{"content_type": "image/jpeg", "file_name": "scan.jpg", "file_size": len(image_bytes)}]},
            headers={"Authorization": f"Bearer {YOUCAM_API_KEY}"},
        )
        resp.raise_for_status()
        return resp

    resp = await _with_retry(_do)
    file_info = resp.json()["data"]["files"][0]
    return file_info["file_id"], file_info["requests"][0]


async def _upload_image(client: httpx.AsyncClient, upload_request: dict, image_bytes: bytes) -> None:
    # upload_request is the {method, url, headers} block YouCam returned —
    # it's a pre-signed S3 URL, so the headers (including Content-Length)
    # must be sent exactly as given or the signature check fails.
    async def _do():
        resp = await client.request(
            upload_request.get("method", "PUT"),
            upload_request["url"],
            content=image_bytes,
            headers=upload_request.get("headers", {}),
        )
        resp.raise_for_status()
        return resp

    await _with_retry(_do)


async def _create_task(client: httpx.AsyncClient, file_id: str, concerns: list[str]) -> str:
    async def _do():
        resp = await client.post(
            f"{YOUCAM_API_BASE}/s2s/v2.0/task/skin-analysis",
            json={"src_file_id": file_id, "dst_actions": concerns},
            headers={"Authorization": f"Bearer {YOUCAM_API_KEY}"},
        )
        resp.raise_for_status()
        return resp

    resp = await _with_retry(_do)
    return resp.json()["data"]["task_id"]


async def _poll_task(client: httpx.AsyncClient, task_id: str, timeout_s: float = 60.0) -> dict:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        resp = await client.get(
            f"{YOUCAM_API_BASE}/s2s/v2.0/task/skin-analysis/{task_id}",
            headers={"Authorization": f"Bearer {YOUCAM_API_KEY}"},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        status = data.get("task_status")
        if status == "success":
            return data
        if status == "error":
            raise RuntimeError(f"YouCam task {task_id} failed: {data.get('error')}")
        await asyncio.sleep(2.0)
    raise TimeoutError(f"YouCam task {task_id} did not complete within {timeout_s}s")


def _load_mock_fixture() -> dict:
    contents = return_file_contents(MOCK_FIXTURE_PATH)
    return json.loads(contents)


async def analyse_skin(image_bytes: bytes, concerns: list[str]) -> SkinAnalysisResult:
    if YOUCAM_MOCK_MODE:
        payload = _load_mock_fixture()
        skin_age, overall = _extract_summary(payload)
        return SkinAnalysisResult(
            metrics=_to_skin_metrics(_extract_scores(payload["results"])),
            skin_age=skin_age,
            overall_score=overall,
            file_id="mock-file-id",
            task_id=f"mock-task-{uuid.uuid4()}",
            raw_payload=payload,
        )

    image_bytes = _validate_and_resize(image_bytes)

    async with httpx.AsyncClient(timeout=30.0) as client:
        file_id, upload_request = await _request_upload_url(client, image_bytes)
        await _upload_image(client, upload_request, image_bytes)
        task_id = await _create_task(client, file_id, concerns)
        raw_payload = await _poll_task(client, task_id)
        scores, output_images, score_info = await _fetch_results(client, raw_payload.get("results"))

    skin_age, overall = _extract_summary(score_info)
    return SkinAnalysisResult(
        metrics=_to_skin_metrics(scores, output_images),
        skin_age=skin_age,
        overall_score=overall,
        file_id=file_id,
        task_id=task_id,
        raw_payload=raw_payload,
    )


def infer_skin_type(metrics: list[SkinMetric]) -> str | None:
    """Skin type from measured oiliness + moisture severity (0 = clear,
    1 = significant). Redness at moderate+ marks skin as sensitive first —
    the tolerance model cares about that more than oil."""
    by_name = {m.name: m.normalised for m in metrics}
    oil, dry, red = by_name.get("oiliness"), by_name.get("moisture"), by_name.get("redness")
    if oil is None or dry is None:
        return None
    if red is not None and red >= 0.5:
        return "sensitive"
    if oil >= 0.5 and dry >= 0.5:
        return "combination"
    if oil >= 0.5:
        return "oily"
    if dry >= 0.5:
        return "dry"
    return "normal"
