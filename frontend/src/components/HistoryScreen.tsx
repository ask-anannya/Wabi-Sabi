import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Loader2, Trash2 } from "lucide-react";
import { deleteScanHistoryEntry, getScanHistory } from "../services/api";
import Card from "./ui/Card";
import type { ScanHistoryEntry } from "../entities/types";

interface HistoryScreenProps {
  userId: string;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

const HistoryScreen: React.FC<HistoryScreenProps> = ({ userId }) => {
  const [entries, setEntries] = useState<ScanHistoryEntry[] | null>(null);
  const [error, setError] = useState<string>("");
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    getScanHistory(userId)
      .then((result) => {
        if (!cancelled) setEntries(result);
      })
      .catch(() => {
        if (!cancelled) setError("Couldn't load your scan history. Please try again.");
      });
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const handleDelete = async (id: number) => {
    if (!window.confirm("Delete this scan? This can't be undone.")) return;
    setDeletingId(id);
    try {
      await deleteScanHistoryEntry(id, userId);
      setEntries((prev) => (prev ? prev.filter((entry) => entry.id !== id) : prev));
    } catch {
      setError("Couldn't delete that scan. Please try again.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col h-full overflow-y-auto p-6 bg-ink"
    >
      <h1 className="text-2xl font-display font-semibold text-gray-100 mb-1">Scan History</h1>
      <p className="text-sm text-gray-500 mb-6">Every scan you've taken, most recent first.</p>

      {error && (
        <p role="alert" className="text-sm text-rose-400 mb-4">
          {error}
        </p>
      )}

      {entries === null && !error && (
        <div className="flex-1 flex items-center justify-center text-gray-500">
          <Loader2 size={28} className="animate-spin" aria-hidden="true" />
        </div>
      )}

      {entries !== null && entries.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center text-center gap-2 text-gray-500">
          <p>No scans yet.</p>
          <p className="text-sm">Take your first scan to see it here.</p>
        </div>
      )}

      {entries && entries.length > 0 && (
        <ul className="space-y-3 max-w-2xl w-full mx-auto">
          {entries.map((entry) => (
            <li key={entry.id}>
              <Card variant="solid" className="p-5 flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-300">{formatDate(entry.created_at)}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Confidence: {Math.round(entry.trust_score * 100)}%
                  </p>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {entry.metrics.map((metric) => (
                      <span
                        key={metric.name}
                        className="text-xs px-2 py-1 rounded-full bg-white/5 border border-white/10 text-gray-300 capitalize"
                      >
                        {metric.name.replace("_", " ")}: {metric.band}
                      </span>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(entry.id)}
                  disabled={deletingId === entry.id}
                  aria-label="Delete this scan"
                  className="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-full text-gray-500 hover:text-rose-400 hover:bg-rose-500/10 transition disabled:opacity-50"
                >
                  {deletingId === entry.id ? (
                    <Loader2 size={16} className="animate-spin" aria-hidden="true" />
                  ) : (
                    <Trash2 size={16} aria-hidden="true" />
                  )}
                </button>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </motion.div>
  );
};

export default HistoryScreen;
