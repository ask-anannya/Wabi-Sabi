from models.hallucination import PrefilterResult
from models.llm_response import LLMResponse
from utils.text_utils import contains_any, is_profile_partial

CLAIMS = {
 "MEDICAL_TERMS" : {
    "terms" : ["diagnose", "diagnosis", "disease", "infection",
    "eczema", "psoriasis", "rosacea", "fungal",
    "bacterial", "prescription", "antibiotic",
    "cure", "heal", "treat","generally safe", "safe and effective",
    "safe for oily skin", "safe for acne", "no side effects",
    "suitable for everyone", "works for all skin types"],
    "score" : 0.4,
    "tag" : "medical_claim"
 },

"ABSOLUTE_TERMS" : {
    "terms" : [
        # Certainty / guarantee
        "always", "guaranteed", "definitely", "certainly",
        "will work", "will fix", "will cure",
        "proven", "clinically proven", "scientifically proven",
        "no side effects", "risk free",

        # Time-bound miracle claims
        "overnight", "instantly", "immediate results",
        "in days", "in 3 days", "in 5 days", "in 7 days",
        "in a week", "in two weeks", "within a week",

        # Percentage / perfection claims
        "100%", "completely", "totally", "permanent",
        "never come back", "eliminates permanently",

        # Overgeneralization words
        "for everyone", "works for all skin types",
        "safe for everyone", "universally safe",
        "anyone can use", "no matter your skin",

        # Regulatory red flags
        "fda approved cure", "dermatologist guaranteed",

        # Soft absolutes that still mislead
        "usually", "generally", "commonly fixes",
        "best solution", "ultimate solution"
    ],
    "score" : 0.2,
    "tag" : "absolute_claim"
 },

"BRAND_NAMES" : {
    "terms" : ["cerave", "the ordinary", "neutrogena",
    "la roche", "olay", "clinique"],
    "score" : 0.3,
    "tag" : "brand_violation"
 },

"RISKY_INGREDIENTS" : {
    "terms" : [
        # Retinoids
        "tretinoin", "retinoic acid",
        "isotretinoin", "accutane",
        "adapalene", "tazarotene",

        # Skin lightening agents
        "hydroquinone", "monobenzone",
        "kojic acid injection", "glutathione injection",

        # Steroids
        "clobetasol", "betnovate",
        "mometasone", "hydrocortisone",
        "steroid cream", "topical steroid",

        # Exfoliants (high risk when misused)
        "glycolic acid 20%", "glycolic acid 30%",
        "salicylic acid 10%", "salicylic acid peel",
        "tca peel", "chemical peel at home",

        # Antibiotics
        "clindamycin", "erythromycin",
        "doxycycline", "minocycline",
        "topical antibiotic",

        # Hormonal / acne meds
        "spironolactone", "oral isotretinoin",

        # Pregnancy risk
        "retinol during pregnancy",
        "vitamin a overdose",

        # Misused cosmetic procedures
        "microneedling at home",
        "dermaroller infection risk",
        "skin needling treatment",

        # Other banned / high-risk agents
        "mercury cream", "whitening injection",
        "bleaching agent for skin"

        # Weak ingredients
        "salicylic acid","glycolic acid",
        "lactic acid","mandelic acid",
        "azelaic acid","aha","bha","pha",
        "chemical exfoliant","acid exfoliant"
    ],
    "score" : 0.4,
    "tag" : "unsafe_ingredient"
 }
}


def get_risk_score(text : str,triggers : list)->float:
    risk_score = 0.0
    if text != "":
      for claim in CLAIMS:
        terms  = CLAIMS[claim]["terms"]
        if contains_any(text, terms):
            risk_score += CLAIMS[claim]["score"]
            triggers.append(CLAIMS[claim]["tag"])
    return risk_score

def wabi_sabi_prefilter(
    llm_response : LLMResponse
) -> PrefilterResult:
    
    triggers = []
    risk_score = 0.0

    routine_mode = llm_response.Type == "routine"
    if routine_mode:
        print("Routine mode detected in prefilter.")
        if is_profile_partial(llm_response.Data.Profile):
            triggers.append("premature_routine")
            risk_score += 0.6
        risk_score += get_risk_score(llm_response.Data.UsageInstructions or "",triggers=triggers)
    else: 
        print("Routine mode not detected in prefilter.")
        risk_score += get_risk_score(llm_response.Data.Response,triggers)      

    risk_score = min(1.0, round(risk_score, 2))

    # Decision threshold (tuned for cost savings)
    should_evaluate = risk_score >= 0.25
    if not should_evaluate:
        triggers.append("safe")

    return PrefilterResult(
         should_evaluate=should_evaluate,
         risk_score=risk_score,
         triggers=triggers
    )