from pydantic import BaseModel, Field


class GroundingClaim(BaseModel):
    text: str
    grounded: bool
    supporting_metric: str | None = None
    note: str = ""


class GroundingResult(BaseModel):
    claims: list[GroundingClaim] = Field(default_factory=list)
    grounding_score: float = 0.0
    unsupported_claims: list[str] = Field(default_factory=list)
    error: str = ""

    @property
    def passed(self) -> bool:
        return not self.error and not self.unsupported_claims and self.grounding_score >= 0.5


class ConsistencyResult(BaseModel):
    consistent: bool = True
    violations: list[str] = Field(default_factory=list)
    violating_categories: list[str] = Field(default_factory=list)


class AmbiguityResult(BaseModel):
    ambiguity: float = 0.0  # 0-1, higher = measurement is closer to a band boundary


class TrustResult(BaseModel):
    score: float
    band: str  # "confident" | "fairly_confident" | "uncertain" | "see_a_dermatologist"
    spoken_line: str
