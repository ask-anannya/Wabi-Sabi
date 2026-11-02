import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Loader2, X } from "lucide-react";
import HonestMatchCard from "./HonestMatchCard";
import { getHonestCheck } from "../services/api";
import type { HonestMatch } from "../entities/types";

interface ProductHonestModalProps {
  productId: string;
  userId: string;
  onClose: () => void;
  onStartUsing?: (productId: string) => void;
}

const ProductHonestModal: React.FC<ProductHonestModalProps> = ({ productId, userId, onClose, onStartUsing }) => {
  const [currentId, setCurrentId] = useState(productId);
  const [match, setMatch] = useState<HonestMatch | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setMatch(null);
    setError("");
    getHonestCheck(currentId, userId)
      .then((res) => {
        if (cancelled) return;
        setMatch(res.match);
      })
      .catch(() => !cancelled && setError("Couldn't run the honest check. Please try again."));
    return () => {
      cancelled = true;
    };
  }, [currentId, userId]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-4"
      onClick={onClose}
      onKeyDown={(e) => e.key === "Escape" && onClose()}
      role="dialog"
      aria-modal="true"
      aria-label="Honest check"
    >
      <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-display font-semibold text-gray-100">Honest check</h2>
          <button onClick={onClose} aria-label="Close" className="w-9 h-9 flex items-center justify-center rounded-full text-gray-400 hover:bg-white/10">
            <X size={18} />
          </button>
        </div>
        {error && <p role="alert" className="text-sm text-rose-400">{error}</p>}
        {!match && !error && (
          <div className="flex justify-center py-12 text-gray-500">
            <Loader2 size={28} className="animate-spin" aria-hidden="true" />
          </div>
        )}
        {match && (
          <HonestMatchCard match={match} defaultExpanded onOpen={setCurrentId} onStartUsing={onStartUsing} />
        )}
        <p className="text-[11px] text-gray-500 mt-3 px-1">
          Popularity says nothing about your skin. What worked for someone else isn't evidence it'll work
          for you: your tolerance and the ingredient facts always decide.
        </p>
      </div>
    </motion.div>
  );
};

export default ProductHonestModal;
