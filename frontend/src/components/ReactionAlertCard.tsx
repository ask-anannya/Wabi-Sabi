import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import { resolveReaction } from "../services/api";
import type { ProfileView, ReactionAlert } from "../entities/types";

interface ReactionAlertCardProps {
  alert: ReactionAlert;
  userId: string;
  onResolved: (view: ProfileView) => void;
}

// A scan noticed redness rising after a new active. The user decides; we
// never lower their tolerance on a scan alone.
const ReactionAlertCard: React.FC<ReactionAlertCardProps> = ({ alert, userId, onResolved }) => {
  const [busy, setBusy] = useState(false);

  const resolve = async (confirmed: boolean) => {
    setBusy(true);
    try {
      onResolved(await resolveReaction(userId, alert.reaction_id, confirmed));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div role="alert" className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20">
      <p className="flex gap-2 text-sm text-amber-100">
        <AlertTriangle size={16} className="flex-shrink-0 mt-0.5 text-amber-300" aria-hidden="true" />
        {alert.text}
      </p>
      <div className="flex gap-2 mt-3">
        <button
          disabled={busy}
          onClick={() => resolve(true)}
          className="text-xs px-3 py-1.5 rounded-full bg-amber-400 text-ink font-medium disabled:opacity-50"
        >
          Yes, it irritated me
        </button>
        <button
          disabled={busy}
          onClick={() => resolve(false)}
          className="text-xs px-3 py-1.5 rounded-full bg-white/10 text-gray-200 disabled:opacity-50"
        >
          No, something else
        </button>
      </div>
    </div>
  );
};

export default ReactionAlertCard;
