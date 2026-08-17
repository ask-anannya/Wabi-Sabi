import { CheckCircle2, CircleHelp, TriangleAlert, Stethoscope } from "lucide-react";
import type { TrustBand } from "../entities/types";

interface TrustLineProps {
  band: TrustBand;
  score: number;
  spokenLine: string;
}

// Distinct icon shape per band (never colour alone) so the confidence read
// still works for colour-blind users and in monochrome contexts.
const BAND_CONFIG: Record<TrustBand, { icon: typeof CheckCircle2; label: string; className: string }> = {
  confident: { icon: CheckCircle2, label: "Confident", className: "text-emerald-300 bg-emerald-500/10 border-emerald-500/25" },
  fairly_confident: { icon: CheckCircle2, label: "Fairly confident", className: "text-amber-300 bg-amber-500/10 border-amber-500/25" },
  uncertain: { icon: CircleHelp, label: "Uncertain", className: "text-amber-200 bg-amber-500/15 border-amber-500/30" },
  see_a_dermatologist: { icon: Stethoscope, label: "See a dermatologist", className: "text-rose-300 bg-rose-500/10 border-rose-500/25" },
};

const TrustLine: React.FC<TrustLineProps> = ({ band, score, spokenLine }) => {
  const config = BAND_CONFIG[band] ?? BAND_CONFIG.uncertain;
  const Icon = config.icon;

  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex items-start gap-3 p-4 rounded-2xl border shadow-soft ${config.className}`}
    >
      {band === "see_a_dermatologist" ? (
        <TriangleAlert size={22} className="shrink-0 mt-0.5" aria-hidden="true" />
      ) : (
        <Icon size={22} className="shrink-0 mt-0.5" aria-hidden="true" />
      )}
      <div>
        <p className="font-semibold text-sm">
          {config.label} <span className="font-normal opacity-70">({Math.round(score * 100)}%)</span>
        </p>
        <p className="text-sm mt-1">{spokenLine}</p>
      </div>
    </div>
  );
};

export default TrustLine;
