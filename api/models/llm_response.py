from models.grounding import TrustResult
from models.profile import HonestMatch, ReactionAlert
from models.user import User
from pydantic import BaseModel, Field
from services.youcam_client import SkinMetric


class DataModel(BaseModel):
    Profile :  User | None = Field(alias="profile",default=None)
    Response : str | None = Field(alias="response",default=None)
    MorningRoutine : list | None = Field(alias="morning_routine",default=None)
    EveningRoutine : list | None = Field(alias="evening_routine",default=None)
    NightRoutine : list | None = Field(alias="night_routine",default=None)
    UsageInstructions : str | None = Field(alias="usage_instructions",default=None)

class LLMResponse(BaseModel):
    Type: str = Field(..., alias="type", description="type of response") # values : "chat", "routine" or "error"
    Data : DataModel = Field(..., alias="data")


class AdviceItem(BaseModel):
    metric: str
    text: str
    recommend: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    grounded: bool = True
    supporting_metric: str | None = None


class ProgressDelta(BaseModel):
    deltas: dict = Field(default_factory=dict)  # metric name -> {direction, change}
    spoken_note: str = ""


class ScanResponse(BaseModel):
    spoken_script: str  # PRIMARY output — full narration, in order
    reading_summary: str = ""  # written form of the opening summary line, for on-screen display
    metrics: list[SkinMetric]
    advice: list[AdviceItem]
    trust: TrustResult
    progress: ProgressDelta | None = None
    honest_matches: list[HonestMatch] = Field(default_factory=list)
    reaction_alerts: list[ReactionAlert] = Field(default_factory=list)
    skin_age: int | None = None  # YouCam score_info.json skin_age
    overall_score: float | None = None  # YouCam all.score, 0-100, higher = healthier
    inferred_skin_type: str | None = None  # from YouCam oiliness/moisture/redness
