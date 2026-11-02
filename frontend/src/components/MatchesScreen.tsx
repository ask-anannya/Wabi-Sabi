import { useCallback, useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2, Search, SlidersHorizontal } from "lucide-react";
import HonestMatchCard from "./HonestMatchCard";
import OnboardingScreen from "./OnboardingScreen";
import ProductHonestModal from "./ProductHonestModal";
import { getCatalog, getMatches, getProfile, startUsage } from "../services/api";
import type { MatchesResult, ProductSummary, UserProfile } from "../entities/types";

interface MatchesScreenProps {
  userId: string;
}

const MatchesScreen: React.FC<MatchesScreenProps> = ({ userId }) => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [editing, setEditing] = useState(false);
  const [result, setResult] = useState<MatchesResult | null>(null);
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const [error, setError] = useState("");

  const loadMatches = useCallback(() => {
    setResult(null);
    getMatches(userId)
      .then(setResult)
      .catch(() => setError("Couldn't load your honest picks. Please try again."));
  }, [userId]);

  useEffect(() => {
    getProfile(userId)
      .then((view) => {
        setProfile(view.profile);
        if (view.profile.onboarded) loadMatches();
      })
      .catch(() => setError("Couldn't load your profile."));
    getCatalog()
      .then((c) => setProducts(c.products))
      .catch(() => undefined);
  }, [userId, loadMatches]);

  const hits = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (term.length < 2) return [];
    return products.filter((p) => `${p.brand} ${p.name}`.toLowerCase().includes(term)).slice(0, 6);
  }, [query, products]);

  const handleStartUsing = async (productId: string) => {
    try {
      await startUsage(userId, productId);
      setToast("Added to your routine. Check in from the Tolerance tab so we can learn how your skin handles it.");
    } catch {
      setToast("Couldn't add that product. Please try again.");
    }
    setTimeout(() => setToast(""), 4000);
  };

  const showOnboarding = profile !== null && (!profile.onboarded || editing);

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col h-full overflow-y-auto p-4 md:p-6 bg-ink"
    >
      {error && <p role="alert" className="text-sm text-rose-400 mb-4">{error}</p>}
      {profile === null && !error && (
        <div className="flex-1 flex items-center justify-center text-gray-500">
          <Loader2 size={28} className="animate-spin" aria-hidden="true" />
        </div>
      )}

      {showOnboarding && (
        <OnboardingScreen
          userId={userId}
          initial={profile}
          onCancel={profile?.onboarded ? () => setEditing(false) : undefined}
          onDone={(view) => {
            setProfile(view.profile);
            setEditing(false);
            loadMatches();
          }}
        />
      )}

      {profile && !showOnboarding && (
        <div className="max-w-2xl w-full mx-auto space-y-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-display font-semibold text-gray-100">Your honest picks</h1>
              <p className="text-sm text-gray-400 mt-1">
                Only products that do what your skin needs, within your tolerance, at a fair price. No hype.
              </p>
              <p className="text-[11px] text-gray-500 mt-2">
                Needs from your YouCam scan · strengths & prices from ingredient lists · buzz tiers are editorial ·
                "people like you" comes from other users' check-ins.
              </p>
            </div>
            <button
              onClick={() => setEditing(true)}
              className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-full bg-white/5 text-gray-300 hover:bg-white/10 flex-shrink-0"
            >
              <SlidersHorizontal size={14} aria-hidden="true" /> Edit profile
            </button>
          </div>

          <section aria-label="Hype check" className="rounded-2xl p-4 bg-gradient-to-br from-coral/10 to-lavender/10 border border-white/10">
            <h2 className="text-sm font-semibold text-gray-100">Hype check</h2>
            <p className="text-xs text-gray-400 mb-2">Saw something on your feed? See if it's worth it for your skin.</p>
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" aria-hidden="true" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. Drunk Elephant, La Mer, C E Ferulic"
                aria-label="Search a product to hype-check"
                className="w-full pl-8 pr-3 py-2 rounded-xl bg-ink/60 border border-white/10 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-brand-500"
              />
            </div>
            {hits.length > 0 && (
              <ul className="mt-1 rounded-xl bg-ink-elevated border border-white/10 overflow-hidden">
                {hits.map((p) => (
                  <li key={p.id}>
                    <button
                      onClick={() => {
                        setOpenId(p.id);
                        setQuery("");
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-gray-200 hover:bg-white/5"
                    >
                      {p.brand} {p.name}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {result && (
            <div className="text-xs text-gray-500 space-y-1">
              <p>
                {result.from_scan ? "Based on your latest scan" : "Based on your profile (scan for sharper picks)"}:{" "}
                {result.needs.slice(0, 4).map((n) => n.label).join(", ")}.
              </p>
              {result.avoiding.length > 0 && <p>Avoiding: {result.avoiding.join(", ").toLowerCase()}.</p>}
            </div>
          )}

          {!result && !error && (
            <div className="flex justify-center py-12 text-gray-500">
              <Loader2 size={28} className="animate-spin" aria-hidden="true" />
            </div>
          )}

          {result && result.matches.length === 0 && (
            <p className="text-sm text-gray-400">
              Nothing in our catalog fits your needs and tolerance right now. That's an honest answer, not a sales pitch.
            </p>
          )}

          <ul className="space-y-3 pb-6">
            {result?.matches.map((m) => (
              <li key={m.product.id}>
                <HonestMatchCard match={m} onOpen={setOpenId} onStartUsing={handleStartUsing} />
              </li>
            ))}
          </ul>
        </div>
      )}

      {toast && (
        <div role="status" className="fixed bottom-4 left-1/2 -translate-x-1/2 max-w-sm text-sm px-4 py-2 rounded-xl bg-ink-elevated border border-white/10 text-gray-100 shadow-lift z-50">
          {toast}
        </div>
      )}

      <AnimatePresence>
        {openId && (
          <ProductHonestModal
            productId={openId}
            userId={userId}
            onClose={() => setOpenId(null)}
            onStartUsing={handleStartUsing}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default MatchesScreen;
