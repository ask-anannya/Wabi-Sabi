export interface RoutineStep {
  step_number: number;
  product_category: string;
  key_ingredients: string[];
  usage_instructions: string;
  frequency: string;
}

export interface Profile {
  age: string;
  skin_type: string;
  concerns: string[];
}

export interface RoutineData {
  profile: Profile;
  warnings: string[];
  morning_routine: RoutineStep[];
  evening_routine: RoutineStep[];
  night_routine: RoutineStep[];
}


export interface RoutineContent {
  type: "routine";
  data: RoutineData;
}

export type MessageContent = string | RoutineContent;

export interface Message {
  role : "human" | "ai";
  content: MessageContent;
}

export interface SkinMetric {
  name: string;
  raw_score: number;
  normalised: number;
  band: "clear" | "mild" | "moderate" | "significant";
  band_distance: number;
  output_image: string | null;
}

export interface AdviceItem {
  metric: string;
  text: string;
  recommend: string[];
  avoid: string[];
  grounded: boolean;
  supporting_metric: string | null;
}

export type TrustBand = "confident" | "fairly_confident" | "uncertain" | "see_a_dermatologist";

export interface TrustResult {
  score: number;
  band: TrustBand;
  spoken_line: string;
}

export interface MetricDelta {
  direction: "improved" | "worsened" | "about_the_same";
  change: number;
}

export interface ProgressDelta {
  deltas: Record<string, MetricDelta>;
  spoken_note: string;
}

export interface ScanResponse {
  spoken_script: string;
  reading_summary: string;
  metrics: SkinMetric[];
  advice: AdviceItem[];
  trust: TrustResult;
  progress: ProgressDelta | null;
  honest_matches: HonestMatch[];
  reaction_alerts: ReactionAlert[];
  skin_age: number | null;
  overall_score: number | null;
  inferred_skin_type: string | null;
}

export type Screen = "landing" | "scan" | "matches" | "tolerance" | "chat" | "history";

// ---- Honest Match (trust engine) ----

export type Tone = "good" | "warn" | "bad" | "neutral";
export type ReasonSource = "youcam" | "catalog" | "you" | "editorial" | "community";

export interface ToleranceLevel {
  proven: number;
  cap: number | null;
}

export interface UserProfile {
  user_id: string;
  skin_type: string | null;
  skin_type_source: "scan" | "you" | null;
  concerns: string[];
  sensitizers: string[];
  tolerance: Record<string, ToleranceLevel>;
  style_prefs: string[];
  onboarded: boolean;
}

export interface Ladder {
  family: string;
  label: string;
  rungs: string[];
  proven: number;
  cap: number | null;
  allowed: number;
}

export interface ProfileView {
  profile: UserProfile;
  ladders: Ladder[];
  message?: string;
}

export interface ProductSummary {
  id: string;
  brand: string;
  name: string;
  category: string;
  price_usd: number;
  size_ml: number;
  key_ingredients: string[];
  strength: string[];
}

export interface Catalog {
  products: ProductSummary[];
  sensitizers: { id: string; label: string }[];
  styles: string[];
}

export interface Reason {
  kind: "need" | "tolerance" | "value" | "hype" | "people_like_you" | "taste" | "dupe";
  label: string;
  text: string;
  tone: Tone;
  source: ReasonSource;
}

export interface HonestMatch {
  product: ProductSummary;
  honest_score: number;
  fits_tolerance: boolean;
  verdict: "great_fit" | "good_fit" | "not_for_you";
  headline: string;
  reasons: Reason[];
  value: { price_per_ml: number; group_median_per_ml: number; ratio: number; overpriced: boolean };
  hype: { popularity: number | null; substance: number; gap: number | null; label: "hyped" | "earned" | "under_the_radar" | "unknown" };
  people_like_you: { affinity: number | null; label: string; text: string } | null;
  taste_affinity: number | null;
  dupe: { kind: "dupe" | "safer"; product: ProductSummary; savings_pct: number; style_overlap: number | null; text: string } | null;
}

export interface MatchesResult {
  matches: HonestMatch[];
  needs: { category: string; label: string; weight: number; from: string[] }[];
  avoiding: string[];
  from_scan: boolean;
}

export interface ReactionAlert {
  reaction_id: number;
  product_id: string;
  product_name: string;
  text: string;
}

export interface UsageEntry {
  product: ProductSummary;
  started_at: string;
  days: number;
}

export type Severity = "fine" | "tingling" | "redness" | "peeling";

export interface AuthUser {
  user_id: string;
  email: string | null;
  name: string | null;
  picture: string | null;
}

export interface ScanHistoryEntry {
  id: number;
  created_at: string;
  metrics: SkinMetric[];
  trust_score: number;
  advice: AdviceItem[];
}
