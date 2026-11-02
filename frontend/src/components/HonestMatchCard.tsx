import { useState } from "react";
import { ChevronDown, Plus, Sparkles } from "lucide-react";
import Card from "./ui/Card";
import type { HonestMatch, ReasonSource, Tone } from "../entities/types";

export const TONE_CLASSES: Record<Tone, string> = {
  good: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
  warn: "bg-amber-500/10 text-amber-300 border-amber-500/20",
  bad: "bg-rose-500/10 text-rose-300 border-rose-500/20",
  neutral: "bg-white/5 text-gray-300 border-white/10",
};

const SOURCE_LABELS: Record<ReasonSource, string> = {
  youcam: "YouCam scan",
  catalog: "Ingredients & price",
  you: "You",
  editorial: "Editorial buzz rating",
  community: "People like you (app reports)",
};

const HYPE_LABELS: Record<HonestMatch["hype"]["label"], string> = {
  hyped: "More hype than substance",
  earned: "Buzz is earned",
  under_the_radar: "Under the radar",
  unknown: "Hype unknown",
};

function scoreColor(score: number, fits: boolean): string {
  if (!fits) return "#f43f5e";
  if (score >= 70) return "#34d399";
  if (score >= 50) return "#5fb4d9";
  return "#fbbf24";
}

export const ScoreRing: React.FC<{ score: number; fits: boolean }> = ({ score, fits }) => {
  const r = 22;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative w-14 h-14 flex-shrink-0" role="img" aria-label={`Honest score ${score} out of 100`}>
      <svg viewBox="0 0 52 52" className="w-14 h-14 -rotate-90">
        <circle cx="26" cy="26" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="5" />
        <circle
          cx="26"
          cy="26"
          r={r}
          fill="none"
          stroke={scoreColor(score, fits)}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={`${(score / 100) * c} ${c}`}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-sm font-semibold text-gray-100">
        {score}
      </span>
    </div>
  );
};

// Buzz (editorial tier) vs substance (evidence + value) on one track: the gap
// between the two markers is the hype gap.
export const HypeMeter: React.FC<{ hype: HonestMatch["hype"] }> = ({ hype }) => {
  if (hype.popularity === null) return null;
  return (
    <div className="mt-3" aria-label={`${HYPE_LABELS[hype.label]}: buzz ${Math.round(hype.popularity * 100)}, substance ${Math.round(hype.substance * 100)}`}>
      <div className="flex justify-between text-[11px] text-gray-500 mb-1">
        <span>Hype meter</span>
        <span>{HYPE_LABELS[hype.label]}</span>
      </div>
      <div className="relative h-2 rounded-full bg-white/5">
        <div
          className="absolute top-0 h-2 rounded-full bg-gradient-to-r from-brand-500/40 to-coral/60"
          style={{
            left: `${Math.min(hype.popularity, hype.substance) * 100}%`,
            width: `${Math.abs(hype.popularity - hype.substance) * 100}%`,
          }}
        />
        <span
          className="absolute -top-1 w-1 h-4 rounded bg-coral"
          style={{ left: `calc(${hype.popularity * 100}% - 2px)` }}
          title="Buzz (editorial)"
        />
        <span
          className="absolute -top-1 w-1 h-4 rounded bg-emerald-400"
          style={{ left: `calc(${hype.substance * 100}% - 2px)` }}
          title="Substance (evidence + value)"
        />
      </div>
      <div className="flex gap-3 text-[11px] text-gray-500 mt-1">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-coral" />Buzz (editorial)</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400" />Substance</span>
      </div>
    </div>
  );
};

interface HonestMatchCardProps {
  match: HonestMatch;
  onOpen?: (productId: string) => void;
  onStartUsing?: (productId: string) => void;
  defaultExpanded?: boolean;
}

const HonestMatchCard: React.FC<HonestMatchCardProps> = ({ match, onOpen, onStartUsing, defaultExpanded = false }) => {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const { product } = match;
  const chips = match.reasons.filter((r) => ["need", "tolerance", "value"].includes(r.kind));

  return (
    <Card variant="solid" className="p-4">
      <div className="flex items-start gap-3">
        <ScoreRing score={match.honest_score} fits={match.fits_tolerance} />
        <div className="flex-1 min-w-0">
          <p className="text-xs uppercase tracking-wide text-gray-500">{product.brand}</p>
          <h3 className="text-base font-semibold text-gray-100 leading-snug">{product.name}</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            ${product.price_usd.toFixed(2)} · {product.size_ml} ml · ${match.value.price_per_ml.toFixed(2)}/ml
          </p>
          {product.strength.length > 0 && (
            <p className="text-xs text-brand-400 mt-1">{product.strength.join(" · ")}</p>
          )}
        </div>
      </div>

      <p className="text-sm text-gray-200 mt-3">{match.headline}</p>

      <div className="flex flex-wrap gap-1.5 mt-3">
        {chips.map((r, i) => (
          <span key={i} className={`text-xs px-2 py-0.5 rounded-full border ${TONE_CLASSES[r.tone]}`}>
            {r.label}
          </span>
        ))}
      </div>

      <HypeMeter hype={match.hype} />

      {match.people_like_you && (
        <p className="text-xs text-gray-400 mt-3 flex gap-1.5">
          <Sparkles size={14} className="text-lavender flex-shrink-0 mt-0.5" aria-hidden="true" />
          {match.people_like_you.text}
        </p>
      )}

      {match.dupe && (
        <button
          onClick={() => onOpen?.(match.dupe!.product.id)}
          className="mt-3 w-full text-left text-xs p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-200 hover:bg-emerald-500/15 transition"
        >
          <span className="font-semibold">
            {match.dupe.kind === "safer"
              ? "Try this instead: "
              : `Honest dupe, ${match.dupe.savings_pct}% less: `}
          </span>
          {match.dupe.product.brand} {match.dupe.product.name}
        </button>
      )}

      <div className="flex items-center justify-between mt-3">
        <button
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200"
        >
          Why? <ChevronDown size={14} className={`transition ${expanded ? "rotate-180" : ""}`} aria-hidden="true" />
        </button>
        {onStartUsing && match.fits_tolerance && (
          <button
            onClick={() => onStartUsing(product.id)}
            className="flex items-center gap-1 text-xs px-3 py-1 rounded-full bg-white/10 text-gray-100 hover:bg-white/20"
          >
            <Plus size={14} aria-hidden="true" /> I'm using this
          </button>
        )}
      </div>

      {expanded && (
        <ul className="mt-3 space-y-2 border-t border-white/5 pt-3">
          {match.reasons.map((r, i) => (
            <li key={i} className="text-sm">
              <div className="flex items-center gap-2">
                <span className={`text-[11px] px-1.5 py-0.5 rounded border ${TONE_CLASSES[r.tone]}`}>{r.label}</span>
                <span className="text-[11px] text-gray-500">{SOURCE_LABELS[r.source]}</span>
              </div>
              <p className="text-gray-300 mt-0.5">{r.text}</p>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
};

export default HonestMatchCard;
