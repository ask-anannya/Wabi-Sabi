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
  metrics: SkinMetric[];
  advice: AdviceItem[];
  trust: TrustResult;
  progress: ProgressDelta | null;
}

export type Screen = "landing" | "scan" | "chat" | "history";

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
