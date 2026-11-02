import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Loader2, X } from "lucide-react";
import Card from "./ui/Card";
import ReactionAlertCard from "./ReactionAlertCard";
import { getPendingReactions, getProfile, getUsage, postCheckin, stopUsage } from "../services/api";
import type { Ladder, ProfileView, ReactionAlert, Severity, UsageEntry } from "../entities/types";

const SEVERITIES: { id: Severity; label: string; className: string }[] = [
  { id: "fine", label: "All good", className: "hover:bg-emerald-500/20 text-emerald-300" },
  { id: "tingling", label: "Tingling", className: "hover:bg-amber-500/20 text-amber-300" },
  { id: "redness", label: "Redness", className: "hover:bg-rose-500/20 text-rose-300" },
  { id: "peeling", label: "Peeling", className: "hover:bg-rose-500/20 text-rose-300" },
];

const LadderView: React.FC<{ ladder: Ladder }> = ({ ladder }) => (
  <div>
    <p className="text-sm text-gray-200 capitalize mb-1.5">{ladder.label}</p>
    <ol className="flex gap-1" aria-label={`${ladder.label} tolerance ladder`}>
      {ladder.rungs.map((rung, i) => {
        const blocked = ladder.cap !== null && i >= ladder.cap;
        const state = blocked ? "blocked" : i <= ladder.proven ? "proven" : i <= ladder.allowed ? "next" : "locked";
        const cls = {
          proven: "bg-emerald-400",
          next: "bg-brand-400/60 ring-1 ring-brand-400",
          locked: "bg-white/10",
          blocked: "bg-rose-500/60",
        }[state];
        const stateText = {
          proven: "proven",
          next: "you can try this",
          locked: "locked until you prove the step below",
          blocked: "irritated your skin",
        }[state];
        return (
          <li key={i} className="flex-1" title={`${rung}: ${stateText}`}>
            <div className={`h-2.5 rounded-full ${cls}`} />
            <span className="sr-only">{`${rung}: ${stateText}`}</span>
          </li>
        );
      })}
    </ol>
  </div>
);

const ToleranceScreen: React.FC<{ userId: string }> = ({ userId }) => {
  const [view, setView] = useState<ProfileView | null>(null);
  const [usage, setUsage] = useState<UsageEntry[]>([]);
  const [alerts, setAlerts] = useState<ReactionAlert[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");

  const reload = useCallback(() => {
    Promise.all([getProfile(userId), getUsage(userId), getPendingReactions(userId)])
      .then(([v, u, a]) => {
        setView(v);
        setUsage(u);
        setAlerts(a);
      })
      .catch(() => setError("Couldn't load your tolerance profile."));
  }, [userId]);

  useEffect(reload, [reload]);

  const handleCheckin = async (productId: string, severity: Severity) => {
    setBusy(productId);
    try {
      const res = await postCheckin(userId, productId, severity);
      setMessage(res.message ?? "");
      reload();
    } catch {
      setError("Couldn't save that check-in.");
    } finally {
      setBusy(null);
    }
  };

  const handleStop = async (productId: string) => {
    await stopUsage(userId, productId).catch(() => undefined);
    reload();
  };

  const touched = view?.ladders.filter((l) => l.proven >= 0 || l.cap !== null) ?? [];
  const untouched = view?.ladders.filter((l) => l.proven < 0 && l.cap === null) ?? [];

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col h-full overflow-y-auto p-4 md:p-6 bg-ink"
    >
      <div className="max-w-2xl w-full mx-auto space-y-5 pb-6">
        <div>
          <h1 className="text-2xl font-display font-semibold text-gray-100">Your tolerance</h1>
          <p className="text-sm text-gray-400 mt-1">
            Every check-in and every scan teaches us what your skin can handle, so you climb one careful step at a time
            instead of burning your skin off.
          </p>
        </div>

        {error && <p role="alert" className="text-sm text-rose-400">{error}</p>}
        {message && (
          <p role="status" className="text-sm p-3 rounded-xl bg-brand-500/10 border border-brand-500/20 text-gray-100">
            {message}
          </p>
        )}

        {alerts.map((a) => (
          <ReactionAlertCard
            key={a.reaction_id}
            alert={a}
            userId={userId}
            onResolved={(res) => {
              setMessage(res.message ?? "");
              reload();
            }}
          />
        ))}

        <section aria-label="Products you're using">
          <h2 className="text-xs uppercase tracking-wide text-gray-500 mb-2">How's your skin with…</h2>
          {view === null && !error && <Loader2 size={20} className="animate-spin text-gray-500" />}
          {view && usage.length === 0 && (
            <p className="text-sm text-gray-500">
              No products tracked yet. Tap "I'm using this" on an honest pick to start learning your tolerance.
            </p>
          )}
          <ul className="space-y-3">
            {usage.map((u) => (
              <li key={u.product.id}>
                <Card className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-xs text-gray-500">{u.product.brand}</p>
                      <p className="text-sm font-medium text-gray-100">{u.product.name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Day {u.days + 1}
                        {u.product.strength.length > 0 && ` · ${u.product.strength.join(" · ")}`}
                      </p>
                    </div>
                    <button onClick={() => handleStop(u.product.id)} aria-label={`Stop tracking ${u.product.name}`} className="text-gray-500 hover:text-gray-300">
                      <X size={16} />
                    </button>
                  </div>
                  <div className="grid grid-cols-4 gap-1.5 mt-3" role="group" aria-label="Log how your skin reacted">
                    {SEVERITIES.map((s) => (
                      <button
                        key={s.id}
                        disabled={busy === u.product.id}
                        onClick={() => handleCheckin(u.product.id, s.id)}
                        className={`text-xs py-2 rounded-xl bg-white/5 border border-white/10 transition disabled:opacity-50 ${s.className}`}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                </Card>
              </li>
            ))}
          </ul>
        </section>

        {view && (
          <section aria-label="Tolerance ladders">
            <h2 className="text-xs uppercase tracking-wide text-gray-500 mb-2">Your ladders</h2>
            <Card className="p-4 space-y-4">
              {[...touched, ...untouched].map((l) => (
                <LadderView key={l.family} ladder={l} />
              ))}
              <div className="flex flex-wrap gap-3 text-[11px] text-gray-500 pt-1">
                <span className="flex items-center gap-1"><span className="w-3 h-2 rounded-full bg-emerald-400" />Proven</span>
                <span className="flex items-center gap-1"><span className="w-3 h-2 rounded-full bg-brand-400/60 ring-1 ring-brand-400" />Safe next step</span>
                <span className="flex items-center gap-1"><span className="w-3 h-2 rounded-full bg-white/10" />Locked</span>
                <span className="flex items-center gap-1"><span className="w-3 h-2 rounded-full bg-rose-500/60" />Irritated you</span>
              </div>
            </Card>
          </section>
        )}
      </div>
    </motion.div>
  );
};

export default ToleranceScreen;
