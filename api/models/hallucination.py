class HallucinationResult:
    hallucination_score : float
    reason : str 
    category : str
    error : str = ""

    def __init__(self, hallucination_score: float = 0, reason: str = "", category: str = "", error: str = "") -> None:
        self.hallucination_score = hallucination_score
        self.reason = reason
        self.category = category
        self.error = error


class PrefilterResult:
    should_evaluate : bool
    risk_score : float
    triggers : list[str]

    def __init__(self, should_evaluate: bool, risk_score: float, triggers: list[str]) -> None:
        self.should_evaluate = should_evaluate
        self.risk_score = risk_score
        self.triggers = triggers