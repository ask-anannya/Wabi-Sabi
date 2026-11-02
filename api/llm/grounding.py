"""
Grounding checker — replaces llm/prefilter.py + llm/hallucination.py on the
scan path (the chat path via POST /llm/chat keeps using those unchanged).

Conceptual shift from the old hallucination detector: we are not scoring how
much the model's free text deviates from plausible language. We are scoring
whether generated advice traces to a metric we actually measured. Three
independent components, combined into one TrustResult:

  4a claim grounding    — does every claim trace to a measured metric?
  4b directional consistency — does the advice match the measured severity?
  4c metric ambiguity   — is the underlying measurement itself borderline?
"""

import os

from domain.advice_bands import ADVICE_BANDS, UNSUPPORTED_TERMS
from llm import LLM
from models.grounding import AmbiguityResult, ConsistencyResult, GroundingClaim, GroundingResult, TrustResult
from services.user_persona_metrics import user_persona_metrics
from services.youcam_client import SkinMetric
from utils.json import safe_json_loads
from utils.text_utils import contains_any

# Carried over from the old llm/prefilter.py CLAIMS["ABSOLUTE_TERMS"]/["MEDICAL_TERMS"].
# A hit here is an immediate grounding failure — no LLM call needed.
ABSOLUTE_TERMS = [
    "always", "guaranteed", "definitely", "certainly",
    "will work", "will fix", "will cure",
    "proven", "clinically proven", "scientifically proven",
    "no side effects", "risk free",
    "overnight", "instantly", "immediate results",
    "in days", "in 3 days", "in 5 days", "in 7 days",
    "in a week", "in two weeks", "within a week",
    "100%", "completely", "totally", "permanent",
    "never come back", "eliminates permanently",
    "for everyone", "works for all skin types",
    "safe for everyone", "universally safe",
    "anyone can use", "no matter your skin",
]

TRUST_BAND_LINES = {
    "confident": "I'm confident in this reading — these results are clear.",
    "fairly_confident": "I'm fairly confident here, though a couple of readings were close to the edge.",
    "uncertain": "I'm not fully certain about this one — treat it as a general pointer, not a firm reading.",
    "see_a_dermatologist": "This is outside what I can confidently read — please see a dermatologist for this.",
}


class GroundingChecker:
    def __init__(self):
        print("Initializing grounding checker...")
        self.llm = LLM(model_name=os.getenv("GROUNDING_MODEL"), prompt_path="prompts/grounding_check.prompt")
        print("Grounding checker initialized.")

    def deterministic_check(self, advice_text: str) -> GroundingResult | None:
        """4a pass 1. Returns a failing GroundingResult if a hard-fail term is
        present, otherwise None (meaning: proceed to the LLM verification pass)."""
        hits = [term for term in ABSOLUTE_TERMS + UNSUPPORTED_TERMS if contains_any(advice_text, [term])]
        if hits:
            return GroundingResult(grounding_score=0.0, unsupported_claims=hits)
        return None

    def llm_check(self, metrics: list[SkinMetric], advice_text: str) -> GroundingResult:
        """4a pass 2. One judge call over surviving text."""
        metrics_summary = [{"name": m.name, "band": m.band, "normalised": m.normalised} for m in metrics]
        prompt = f"Measured metrics: {metrics_summary}\nAdvice: {advice_text}\nEvaluate grounding."
        # One retry: seen live, the judge call occasionally drops the connection
        # ("Server disconnected"), and a failed check scores grounding as 0,
        # which would misreport a clean reading as low-confidence.
        last_error: Exception | None = None
        for _attempt in range(2):
            try:
                llm_response = self.llm.chat_model.generate_content(prompt)
                res_dict = safe_json_loads(llm_response.text)
                claims = [GroundingClaim(**c) for c in res_dict.get("claims", [])]
                return GroundingResult(
                    claims=claims,
                    grounding_score=float(res_dict.get("grounding_score", 0.0)),
                    unsupported_claims=res_dict.get("unsupported_claims", []),
                )
            except Exception as e:
                last_error = e
                print(f"Error during grounding check: {e}")
        return GroundingResult(error=str(last_error))

    def check_claims(self, metrics: list[SkinMetric], advice_text: str) -> GroundingResult:
        deterministic_result = self.deterministic_check(advice_text)
        if deterministic_result is not None:
            return deterministic_result
        return self.llm_check(metrics, advice_text)


def check_consistency(advice_categories: list[str], metric_bands: dict[str, str]) -> ConsistencyResult:
    """4b — fully deterministic, no LLM. Recommending a category on the
    `avoid` list for the measured band is a consistency failure."""
    violations = []
    violating_categories = []
    for metric_name, band in metric_bands.items():
        band_config = ADVICE_BANDS.get(metric_name)
        if not band_config:
            continue
        avoid = band_config.get("avoid", {}).get(band, [])
        for category in advice_categories:
            if category in avoid:
                violations.append(f"{category} is on the avoid list for {metric_name} at {band}")
                violating_categories.append(category)
    return ConsistencyResult(
        consistent=not violations,
        violations=violations,
        violating_categories=violating_categories,
    )


def compute_ambiguity(metrics: list[SkinMetric]) -> AmbiguityResult:
    """4c — no model call. Direct replacement for the old HallucinationScore:
    instead of scoring the model's uncertainty, score the measurement's
    uncertainty. Band width is 0.25, so max distance from a boundary within
    a band is 0.125 (band centre)."""
    if not metrics:
        return AmbiguityResult(ambiguity=0.0)
    per_metric = [max(0.0, 1.0 - (m.band_distance / 0.125)) for m in metrics]
    return AmbiguityResult(ambiguity=round(sum(per_metric) / len(per_metric), 3))


def compose_trust(
    grounding_score: float,
    consistency: ConsistencyResult,
    ambiguity: AmbiguityResult,
    persona_concerns: list[str],
) -> TrustResult:
    """4d — weighted composition, divided by persona risk so the same advice
    yields lower stated confidence for higher-risk personas."""
    w1, w2, w3 = _trust_weights()
    consistency_score = 0.0 if not consistency.consistent else 1.0
    raw_confidence = w1 * grounding_score + w2 * consistency_score + w3 * (1 - ambiguity.ambiguity)

    persona_risk_multiplier = 1.0
    if persona_concerns:
        weights = [
            user_persona_metrics.PERSONA_RISK_WEIGHTS.get(c, 1.5) for c in persona_concerns
        ]
        persona_risk_multiplier = sum(weights) / len(weights)

    score = max(0.0, min(1.0, raw_confidence / persona_risk_multiplier))
    band = _band_for_score(score)
    return TrustResult(score=round(score, 3), band=band, spoken_line=TRUST_BAND_LINES[band])


def _trust_weights() -> tuple[float, float, float]:
    raw = os.getenv("TRUST_WEIGHTS", "0.4,0.4,0.2")
    parts = [float(p) for p in raw.split(",")]
    if len(parts) != 3:
        raise EnvironmentError("TRUST_WEIGHTS must be three comma-separated floats, e.g. 0.4,0.4,0.2")
    return parts[0], parts[1], parts[2]


def _band_for_score(score: float) -> str:
    if score >= 0.8:
        return "confident"
    if score >= 0.6:
        return "fairly_confident"
    if score >= 0.4:
        return "uncertain"
    return "see_a_dermatologist"


if os.getenv("GROUNDING_MODEL"):
    grounding_checker = GroundingChecker()
else:
    raise EnvironmentError("GROUNDING_MODEL environment variable must be set.")
