from llm.grounding import compose_trust
from models.grounding import AmbiguityResult, ConsistencyResult


def _compose(persona_concerns):
    return compose_trust(
        grounding_score=1.0,
        consistency=ConsistencyResult(consistent=True, violations=[], violating_categories=[]),
        ambiguity=AmbiguityResult(ambiguity=0.0),
        persona_concerns=persona_concerns,
    )


def test_sensitive_persona_lowers_confidence_vs_normal():
    normal = _compose(["normal"])
    sensitive = _compose(["sensitive"])
    assert sensitive.score < normal.score


def test_teen_persona_lowers_confidence_vs_normal():
    normal = _compose(["normal"])
    teen = _compose(["teen"])
    assert teen.score < normal.score


def test_no_concerns_uses_no_persona_penalty():
    no_concerns = _compose([])
    normal = _compose(["normal"])
    assert no_concerns.score == normal.score
