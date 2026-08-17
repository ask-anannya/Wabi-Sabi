import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import type { ProgressDelta } from "../entities/types";

interface ProgressViewProps {
  progress: ProgressDelta;
}

const DIRECTION_CONFIG = {
  improved: { icon: TrendingDown, label: "Improved", className: "text-emerald-400" },
  worsened: { icon: TrendingUp, label: "Worsened", className: "text-rose-400" },
  about_the_same: { icon: Minus, label: "About the same", className: "text-gray-500" },
} as const;

const ProgressView: React.FC<ProgressViewProps> = ({ progress }) => {
  const entries = Object.entries(progress.deltas);
  if (entries.length === 0) return null;

  return (
    <section aria-label="Progress since last scan" className="mt-4">
      {progress.spoken_note && (
        <p className="text-sm text-gray-300 mb-2">{progress.spoken_note}</p>
      )}
      <ul className="space-y-1">
        {entries.map(([metric, delta]) => {
          const config = DIRECTION_CONFIG[delta.direction];
          const Icon = config.icon;
          return (
            <li key={metric} className={`flex items-center gap-2 text-sm ${config.className}`}>
              <Icon size={16} aria-hidden="true" />
              <span className="capitalize">{metric.replace("_", " ")}</span>
              <span className="opacity-70">— {config.label}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
};

export default ProgressView;
