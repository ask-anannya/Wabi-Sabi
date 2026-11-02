from llm import wabi_sabi_llm, wabi_sabi_scan_llm
from llm.grounding import check_consistency, compose_trust, compute_ambiguity, grounding_checker
from llm.hallucination import hallucination_detector
from llm.prefilter import wabi_sabi_prefilter
from domain.advice_bands import ADVICE_BANDS
from models.llm_response import AdviceItem, LLMResponse, ProgressDelta, ScanResponse
from models.profile import HonestMatch, ReactionAlert
from models.user import User
from services import catalog, profile_store, scan_store, tolerance, trust_engine, youcam_client
from services.llm_datadog_metrics import llm_metrics
from services.user_persona_metrics import user_persona_metrics
from utils.ai_msg import get_vertex_ai_message
from utils.json import safe_json_loads
from utils.user_msg import get_recent_user_message

async def llm_chat(payload: dict)->LLMResponse:
        # Call the Wabi-Sabi LLM chat model
        res = wabi_sabi_llm.vertex_chat(payload)
        llm_metrics.logging_event("chats.total",1)
        llm_response : LLMResponse = get_vertex_ai_message(res)

        if llm_response.Type == "error":
                llm_metrics.log_error("json_parsing_failure")
                llm_metrics.logging_event("hallucination.score",1)
                return llm_response

        try: 
                # Check if hallucination detection is required
                prefilter_result = wabi_sabi_prefilter(llm_response)
                recent_user_msgs = get_recent_user_message(payload)
                print(f"Prefilter result: Risk Score={prefilter_result.risk_score}, Triggers={prefilter_result.triggers}, Should Evaluate={prefilter_result.should_evaluate}")
                llm_metrics.log_prefilter(prefilter_result.risk_score, prefilter_result.triggers)
                if prefilter_result.should_evaluate:
                   print("Prefilter triggered hallucination detection.")
                   hallucination = hallucination_detector.detect_hallucination(recent_user_msgs, llm_response.Data.Response) 
                   llm_metrics.log_hallucination(hallucination)

                   if hallucination.hallucination_score > 0.5:
                        user_persona_metrics.log_user_affected()
                        if llm_response.Data.Profile is not None:
                          user_persona_metrics.emit_persona_risk(llm_response.Data.Profile)                     
                         


        except Exception as e:
                llm_metrics.log_error("hallucination_detection_failure")
                print(f"Error logging hallucination metrics: {e}")
                return LLMResponse(type="error",data={"response":"something went wrong"})
        return llm_response


def _allowed_categories_for(metrics: list[youcam_client.SkinMetric]) -> dict:
    allowed = {}
    for metric in metrics:
        band_config = ADVICE_BANDS.get(metric.name)
        if not band_config:
            continue
        allowed[metric.name] = {
            "band": metric.band,
            "recommend": band_config.get("recommend", {}).get(metric.band, []),
            "avoid": band_config.get("avoid", {}).get(metric.band, []),
        }
    return allowed


def _generate_scan_advice(
    metrics: list[youcam_client.SkinMetric], profile: User, deltas: dict
) -> tuple[str, list[AdviceItem], str, bool]:
    payload = {
        "metrics": [m.model_dump(exclude={"output_image"}) for m in metrics],
        "allowed_categories": _allowed_categories_for(metrics),
        "profile": profile.model_dump() if profile else None,
        "deltas": deltas,
    }
    llm_response = wabi_sabi_scan_llm.chat_model.generate_content(str(payload))
    res_dict = safe_json_loads(llm_response.text)
    data = res_dict.get("data", {})
    reading_summary = data.get("reading_summary", "")
    progress_note = data.get("progress_note", "")
    derm_referral = bool(data.get("derm_referral", False))

    advice_items = [
        AdviceItem(
            metric=item.get("metric", ""),
            text=item.get("text", ""),
            recommend=item.get("recommend", []),
            avoid=item.get("avoid", []),
        )
        for item in data.get("advice", [])
    ]
    return reading_summary, advice_items, progress_note, derm_referral


async def _honest_layer(
    user_id: str, deltas: dict, metrics: list[youcam_client.SkinMetric]
) -> tuple[list[HonestMatch], list[ReactionAlert], str | None]:
    """Everything this scan teaches the tolerance model, plus the top honest
    matches. Best-effort like the history read: a failure here must not cost
    the user their scan.
      - skin type is inferred from YouCam oiliness/moisture/redness unless
        the user set it themselves;
      - an irritation reading (redness, texture, dryness) that worsened after
        starting an active logs an unconfirmed reaction for the user to confirm."""
    try:
        profile = profile_store.get_profile(user_id)
        inferred = youcam_client.infer_skin_type(metrics)
        if inferred and profile.skin_type_source != "you" and inferred != profile.skin_type:
            profile = profile_store.save_profile(
                profile.model_copy(update={"skin_type": inferred, "skin_type_source": "scan"}))

        usage = [(catalog.get(u.product_id), u.started_at) for u in profile_store.active_usage(user_id)]
        severity = tolerance.scan_severity(tolerance.irritation_readings(deltas))
        alerts = []
        for product in tolerance.scan_reaction_suspects(deltas, [(p, s) for p, s in usage if p]):
            record = profile_store.log_reaction(user_id, product.id, severity, source="scan", confirmed=False)
            alerts.append(tolerance.reaction_alert(record.id, product, severity))

        stored = [m.model_dump(exclude={"output_image"}) for m in metrics]
        result = await trust_engine.honest_matches(profile, stored, limit=3)
        return result["matches"], alerts, inferred
    except Exception as e:
        print(f"[analyse_and_advise] honest layer failed, returning scan without matches: {e}")
        return [], [], None


async def analyse_and_advise(image_bytes: bytes, profile: User, user_id: str) -> ScanResponse:
    concerns = list(ADVICE_BANDS.keys())
    scan_result = await youcam_client.analyse_skin(image_bytes, concerns)
    llm_metrics.log_scan_event("scan.total", 1)

    metrics_for_storage = [m.model_dump(exclude={"output_image"}) for m in scan_result.metrics]

    # History read is a best-effort enhancement (progress-tracking), not core
    # to a single scan's grounded advice — on hosts where SQLite isn't
    # reliably writable (e.g. serverless with an ephemeral filesystem), a
    # scan should still return a full result rather than fail entirely.
    deltas = {}
    try:
        previous_scan = scan_store.get_last_scan(user_id)
        if previous_scan is not None:
            deltas = scan_store.compute_deltas(previous_scan.metrics_json, metrics_for_storage)
    except Exception as e:
        print(f"[analyse_and_advise] get_last_scan failed, continuing without progress: {e}")

    reading_summary, advice_items, progress_note, derm_referral = _generate_scan_advice(
        scan_result.metrics, profile, deltas
    )

    advice_text = " ".join(item.text for item in advice_items)
    grounding_result = grounding_checker.check_claims(scan_result.metrics, advice_text)
    llm_metrics.log_scan_gauge("grounding.score", grounding_result.grounding_score)

    metric_bands = {m.name: m.band for m in scan_result.metrics}
    advice_categories = [c for item in advice_items for c in (item.recommend + item.avoid)]
    consistency_result = check_consistency(advice_categories, metric_bands)
    if consistency_result.violations:
        llm_metrics.log_scan_event("consistency.violations", len(consistency_result.violations))

    # Hard rule: strip claims that failed grounding or landed a consistency
    # violation rather than voicing them with a low-confidence caveat.
    if not grounding_result.passed or consistency_result.violations:
        stripped = 0
        kept_items = []
        for item in advice_items:
            unsupported = any(claim in item.text for claim in grounding_result.unsupported_claims)
            inconsistent = any(c in consistency_result.violating_categories for c in item.avoid + item.recommend)
            if unsupported or inconsistent:
                stripped += 1
                continue
            kept_items.append(item)
        advice_items = kept_items
        if stripped:
            llm_metrics.log_scan_event("grounding.claims_stripped", stripped)

    ambiguity_result = compute_ambiguity(scan_result.metrics)
    llm_metrics.log_scan_gauge("metric.ambiguity", ambiguity_result.ambiguity)

    trust = compose_trust(
        grounding_score=grounding_result.grounding_score,
        consistency=consistency_result,
        ambiguity=ambiguity_result,
        persona_concerns=(profile.Concerns or []) if profile else [],
    )
    llm_metrics.log_scan_gauge("trust.score", trust.score, tags=[f"trust.band:{trust.band}"])

    if profile is not None and profile.Concerns:
        user_persona_metrics.emit_persona_risk(profile)

    script_parts = [reading_summary]
    script_parts.extend(item.text for item in advice_items)
    progress = None
    if deltas:
        progress = ProgressDelta(deltas=deltas, spoken_note=progress_note)
        if progress_note:
            script_parts.append(progress_note)
    if derm_referral or trust.band == "see_a_dermatologist":
        script_parts.append("Please see a dermatologist for a proper evaluation.")
    script_parts.append(trust.spoken_line)

    honest, reaction_alerts, inferred_skin_type = await _honest_layer(user_id, deltas, scan_result.metrics)
    script_parts.extend(alert.text for alert in reaction_alerts)
    if honest:
        top = honest[0].product
        script_parts.append(f"Your top honest match is {top.brand} {top.name}.")
    spoken_script = " ".join(part for part in script_parts if part)

    # output_image (base64 PNG, can be ~1MB per metric) is kept in the live
    # ScanResponse below but excluded from persisted history to keep the
    # SQLite scan store lean. Same best-effort reasoning as the read above —
    # a failed save must not cost the user their (already-computed) result.
    try:
        scan_store.save_scan(
            user_id=user_id,
            metrics=metrics_for_storage,
            trust_score=trust.score,
            advice=[a.model_dump() for a in advice_items],
        )
    except Exception as e:
        print(f"[analyse_and_advise] save_scan failed, this scan won't appear in history: {e}")

    return ScanResponse(
        spoken_script=spoken_script,
        reading_summary=reading_summary,
        metrics=scan_result.metrics,
        advice=advice_items,
        trust=trust,
        progress=progress,
        honest_matches=honest,
        reaction_alerts=reaction_alerts,
        skin_age=scan_result.skin_age,
        overall_score=scan_result.overall_score,
        inferred_skin_type=inferred_skin_type,
    )