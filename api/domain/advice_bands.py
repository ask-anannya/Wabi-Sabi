"""
Static metric-band -> advice-category lookup. This is the deterministic
backbone the grounding checker verifies against (api/llm/grounding.py) — the
LLM never invents this mapping, it only speaks in the categories listed here.

One entry per metric implemented in api/services/youcam_client.py's
METRIC_CONFIG. Categories are abstract ingredient/property classes, never
brand names (carries over the old prefilter's BRAND_NAMES constraint).
"""

ADVICE_BANDS = {
    # Normalised severity here still means "dryness severity" (0=clear,
    # 1=significant) — the raw YouCam field is called "moisture" (higher
    # raw = more hydrated), so it's inverted during normalisation
    # (METRIC_CONFIG's polarity="higher_is_better") before reaching bands.
    "moisture": {
        "bands": {"clear": (0.0, 0.25), "mild": (0.25, 0.5), "moderate": (0.5, 0.75), "significant": (0.75, 1.0)},
        "recommend": {
            "mild": ["hydrating", "fragrance_free"],
            "moderate": ["hydrating", "fragrance_free", "barrier_repair"],
            "significant": ["hydrating", "barrier_repair", "derm_referral"],
        },
        "avoid": {
            "moderate": ["high_pct_exfoliant", "alcohol_denat"],
            "significant": ["high_pct_exfoliant", "alcohol_denat", "retinoid_escalation"],
        },
    },
    "wrinkle": {
        "bands": {"clear": (0.0, 0.25), "mild": (0.25, 0.5), "moderate": (0.5, 0.75), "significant": (0.75, 1.0)},
        "recommend": {
            "mild": ["antioxidant", "sunscreen_strict"],
            "moderate": ["antioxidant", "sunscreen_strict", "retinoid_gradual"],
            "significant": ["sunscreen_strict", "retinoid_gradual", "derm_referral"],
        },
        "avoid": {
            "moderate": ["harsh_scrub"],
            "significant": ["harsh_scrub", "retinoid_escalation"],
        },
    },
    "redness": {
        "bands": {"clear": (0.0, 0.25), "mild": (0.25, 0.5), "moderate": (0.5, 0.75), "significant": (0.75, 1.0)},
        "recommend": {
            "mild": ["fragrance_free", "gentle_cleanser"],
            "moderate": ["fragrance_free", "gentle_cleanser", "barrier_repair"],
            "significant": ["fragrance_free", "barrier_repair", "derm_referral"],
        },
        "avoid": {
            "moderate": ["high_pct_exfoliant", "harsh_scrub"],
            "significant": ["high_pct_exfoliant", "harsh_scrub", "retinoid_escalation"],
        },
    },
    "age_spot": {
        "bands": {"clear": (0.0, 0.25), "mild": (0.25, 0.5), "moderate": (0.5, 0.75), "significant": (0.75, 1.0)},
        "recommend": {
            "mild": ["vitamin_c", "sunscreen_strict"],
            "moderate": ["vitamin_c", "sunscreen_strict", "brightening"],
            "significant": ["sunscreen_strict", "brightening", "derm_referral"],
        },
        "avoid": {
            "significant": ["retinoid_escalation"],
        },
    },
    "acne": {
        "bands": {"clear": (0.0, 0.25), "mild": (0.25, 0.5), "moderate": (0.5, 0.75), "significant": (0.75, 1.0)},
        "recommend": {
            "mild": ["oil_control", "non_comedogenic"],
            "moderate": ["oil_control", "non_comedogenic", "exfoliant_mild"],
            "significant": ["non_comedogenic", "derm_referral"],
        },
        "avoid": {
            "moderate": ["occlusive_heavy"],
            "significant": ["occlusive_heavy", "high_pct_exfoliant", "harsh_scrub"],
        },
    },
    "pore": {
        "bands": {"clear": (0.0, 0.25), "mild": (0.25, 0.5), "moderate": (0.5, 0.75), "significant": (0.75, 1.0)},
        "recommend": {
            "mild": ["oil_control", "pore_minimizing"],
            "moderate": ["oil_control", "pore_minimizing", "exfoliant_mild"],
            "significant": ["oil_control", "pore_minimizing", "derm_referral"],
        },
        "avoid": {
            "significant": ["occlusive_heavy"],
        },
    },
    # Normalised severity for the metrics below likewise means "more of the
    # problem": oilier, duller, rougher, less firm, puffier under the eyes.
    "oiliness": {
        "bands": {"clear": (0.0, 0.25), "mild": (0.25, 0.5), "moderate": (0.5, 0.75), "significant": (0.75, 1.0)},
        "recommend": {
            "mild": ["oil_control"],
            "moderate": ["oil_control", "non_comedogenic"],
            "significant": ["oil_control", "non_comedogenic", "pore_minimizing"],
        },
        "avoid": {
            "moderate": ["occlusive_heavy"],
            "significant": ["occlusive_heavy"],
        },
    },
    "radiance": {
        "bands": {"clear": (0.0, 0.25), "mild": (0.25, 0.5), "moderate": (0.5, 0.75), "significant": (0.75, 1.0)},
        "recommend": {
            "mild": ["antioxidant", "sunscreen_strict"],
            "moderate": ["vitamin_c", "antioxidant", "exfoliant_mild"],
            "significant": ["vitamin_c", "exfoliant_mild", "sunscreen_strict"],
        },
        "avoid": {},
    },
    "texture": {
        "bands": {"clear": (0.0, 0.25), "mild": (0.25, 0.5), "moderate": (0.5, 0.75), "significant": (0.75, 1.0)},
        "recommend": {
            "mild": ["exfoliant_mild", "hydrating"],
            "moderate": ["exfoliant_mild", "retinoid_gradual", "hydrating"],
            "significant": ["retinoid_gradual", "barrier_repair", "derm_referral"],
        },
        "avoid": {
            "significant": ["harsh_scrub", "high_pct_exfoliant"],
        },
    },
    "firmness": {
        "bands": {"clear": (0.0, 0.25), "mild": (0.25, 0.5), "moderate": (0.5, 0.75), "significant": (0.75, 1.0)},
        "recommend": {
            "mild": ["antioxidant", "sunscreen_strict"],
            "moderate": ["retinoid_gradual", "antioxidant", "sunscreen_strict"],
            "significant": ["retinoid_gradual", "sunscreen_strict", "derm_referral"],
        },
        "avoid": {},
    },
    "eye_bag": {
        "bands": {"clear": (0.0, 0.25), "mild": (0.25, 0.5), "moderate": (0.5, 0.75), "significant": (0.75, 1.0)},
        "recommend": {
            "mild": ["hydrating", "fragrance_free"],
            "moderate": ["hydrating", "fragrance_free"],
            "significant": ["hydrating", "fragrance_free", "derm_referral"],
        },
        "avoid": {},
    },
}

# Seeded from the old llm/prefilter.py MEDICAL_TERMS list. Anything outside
# this set is unsupported by definition, regardless of how plausible it
# sounds — measurements never speak to cause, diagnosis, or treatment.
SUPPORTED_CLAIMS = {
    "moisture_level",
    "wrinkle_severity",
    "redness_level",
    "pigmentation_level",
    "acne_severity",
    "pore_visibility",
    "oiliness_level",
    "radiance_level",
    "texture_level",
    "firmness_level",
    "eye_bag_level",
}

UNSUPPORTED_TERMS = [
    "diagnose", "diagnosis", "disease", "infection",
    "eczema", "psoriasis", "rosacea", "fungal",
    "bacterial", "prescription", "antibiotic",
    "cure", "heal", "treat", "hormonal", "hormone",
    "allergy", "allergic", "diet", "dermatitis",
]
