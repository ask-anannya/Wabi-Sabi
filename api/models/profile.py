from pydantic import BaseModel, Field


class Active(BaseModel):
    family: str
    form: str
    pct: float | None = None  # None = brand doesn't disclose


class Product(BaseModel):
    id: str
    brand: str
    name: str
    category: str
    size_ml: float
    price_usd: float
    actives: list[Active] = Field(default_factory=list)
    key_ingredients: list[str] = Field(default_factory=list)
    sensitizers: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    evidence: str = "moderate"
    rinse_off: bool = False
    occlusive: bool = False

    @property
    def price_per_ml(self) -> float:
        return self.price_usd / self.size_ml

    @property
    def primary_family(self) -> str | None:
        return self.actives[0].family if self.actives else None

    @property
    def undisclosed(self) -> bool:
        return any(a.pct is None for a in self.actives)


class ToleranceLevel(BaseModel):
    # proven: highest rung the user has used without a bad reaction (-1 = none yet).
    # cap: lowest rung that has caused a bad reaction — never recommended again.
    proven: int = -1
    cap: int | None = None


class UserProfile(BaseModel):
    user_id: str
    skin_type: str | None = None
    skin_type_source: str | None = None  # "scan" (inferred from YouCam) | "you" (self-reported)
    concerns: list[str] = Field(default_factory=list)
    sensitizers: list[str] = Field(default_factory=list)
    tolerance: dict[str, ToleranceLevel] = Field(default_factory=dict)
    style_prefs: list[str] = Field(default_factory=list)  # catalog.STYLES
    onboarded: bool = False


class Reason(BaseModel):
    kind: str  # need | tolerance | value | hype | people_like_you | taste | dupe
    label: str
    text: str
    tone: str = "neutral"  # good | warn | bad | neutral
    source: str  # youcam | catalog | you | editorial | community


class ValueInfo(BaseModel):
    price_per_ml: float
    group_median_per_ml: float
    ratio: float
    overpriced: bool


class HypeInfo(BaseModel):
    popularity: float | None  # editorial buzz tier as 0-1 (brands.json)
    substance: float  # evidence x value, 0-1
    gap: float | None
    label: str  # hyped | earned | under_the_radar | unknown


class PeopleLikeYou(BaseModel):
    affinity: float | None  # share of the cohort that tolerated it
    label: str  # tolerated | reacted | mixed | unknown
    text: str


class ProductSummary(BaseModel):
    id: str
    brand: str
    name: str
    category: str
    price_usd: float
    size_ml: float
    key_ingredients: list[str]
    strength: list[str] = Field(default_factory=list)  # human ladder labels per active


class Dupe(BaseModel):
    kind: str = "dupe"  # dupe = same strength, cheaper | safer = a strength you can handle
    product: ProductSummary
    savings_pct: int
    style_overlap: float | None
    text: str


class HonestMatch(BaseModel):
    product: ProductSummary
    honest_score: int  # 0-100
    fits_tolerance: bool
    verdict: str  # great_fit | good_fit | not_for_you
    headline: str
    reasons: list[Reason]
    value: ValueInfo
    hype: HypeInfo
    people_like_you: PeopleLikeYou | None = None
    taste_affinity: float | None = None
    dupe: Dupe | None = None


class ReactionAlert(BaseModel):
    reaction_id: int
    product_id: str
    product_name: str
    text: str
