import { useEffect, useMemo, useState } from "react";
import { Search, X } from "lucide-react";
import Button from "./ui/Button";
import Card from "./ui/Card";
import { getCatalog, submitQuiz } from "../services/api";
import type { Catalog, ProductSummary, ProfileView, UserProfile } from "../entities/types";

const SKIN_TYPES = ["dry", "oily", "combination", "normal", "sensitive"];
const CONCERNS: { id: string; label: string }[] = [
  { id: "wrinkle", label: "Fine lines" },
  { id: "acne", label: "Breakouts" },
  { id: "redness", label: "Redness" },
  { id: "age_spot", label: "Dark spots" },
  { id: "moisture", label: "Dryness" },
  { id: "pore", label: "Visible pores" },
];

const Chip: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode }> = ({ active, onClick, children }) => (
  <button
    type="button"
    onClick={onClick}
    aria-pressed={active}
    className={`text-sm px-3 py-1.5 rounded-full border transition ${
      active ? "bg-brand-500/20 border-brand-500 text-gray-100" : "bg-white/5 border-white/10 text-gray-400 hover:text-gray-200"
    }`}
  >
    {children}
  </button>
);

const ProductPicker: React.FC<{
  label: string;
  hint: string;
  products: ProductSummary[];
  selected: string[];
  onChange: (ids: string[]) => void;
}> = ({ label, hint, products, selected, onChange }) => {
  const [q, setQ] = useState("");
  const hits = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (term.length < 2) return [];
    return products
      .filter((p) => !selected.includes(p.id) && `${p.brand} ${p.name}`.toLowerCase().includes(term))
      .slice(0, 6);
  }, [q, products, selected]);
  const byId = useMemo(() => Object.fromEntries(products.map((p) => [p.id, p])), [products]);

  return (
    <div>
      <p className="text-sm font-medium text-gray-200">{label}</p>
      <p className="text-xs text-gray-500 mb-2">{hint}</p>
      <div className="flex flex-wrap gap-1.5 mb-2">
        {selected.map((id) => (
          <span key={id} className="flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-white/10 text-gray-200">
            {byId[id]?.brand} {byId[id]?.name}
            <button type="button" onClick={() => onChange(selected.filter((s) => s !== id))} aria-label={`Remove ${byId[id]?.name}`}>
              <X size={12} />
            </button>
          </span>
        ))}
      </div>
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" aria-hidden="true" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search products, e.g. retinol"
          aria-label={label}
          className="w-full pl-8 pr-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-brand-500"
        />
      </div>
      {hits.length > 0 && (
        <ul className="mt-1 rounded-xl bg-ink-elevated border border-white/10 overflow-hidden">
          {hits.map((p) => (
            <li key={p.id}>
              <button
                type="button"
                onClick={() => {
                  onChange([...selected, p.id]);
                  setQ("");
                }}
                className="w-full text-left px-3 py-2 text-sm text-gray-200 hover:bg-white/5"
              >
                {p.brand} {p.name}
                {p.strength.length > 0 && <span className="block text-xs text-gray-500">{p.strength.join(" · ")}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

interface OnboardingScreenProps {
  userId: string;
  initial: UserProfile | null;
  onDone: (view: ProfileView) => void;
  onCancel?: () => void;
}

const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ userId, initial, onDone, onCancel }) => {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  // A scan-detected skin type is shown but not submitted as self-reported unless the user picks one.
  const [skinType, setSkinType] = useState<string | null>(
    initial?.skin_type_source === "you" ? initial.skin_type : null
  );
  const [concerns, setConcerns] = useState<string[]>(initial?.concerns ?? []);
  const [sensitizers, setSensitizers] = useState<string[]>(initial?.sensitizers ?? []);
  const [styles, setStyles] = useState<string[]>(initial?.style_prefs ?? []);
  const [burned, setBurned] = useState<string[]>([]);
  const [worked, setWorked] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getCatalog().then(setCatalog).catch(() => setError("Couldn't load the product list."));
  }, []);

  const toggle = (list: string[], set: (v: string[]) => void, id: string) =>
    set(list.includes(id) ? list.filter((x) => x !== id) : [...list, id]);

  const handleSubmit = async () => {
    setSaving(true);
    setError("");
    try {
      const view = await submitQuiz(
        userId,
        { skin_type: skinType, concerns, sensitizers, style_prefs: styles },
        burned,
        worked
      );
      onDone(view);
    } catch {
      setError("Couldn't save your profile. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl w-full mx-auto space-y-4">
      <div>
        <h1 className="text-2xl font-display font-semibold text-gray-100">Let's learn your skin</h1>
        <p className="text-sm text-gray-400 mt-1">
          What worked for an influencer won't necessarily work for you. Tell us what your skin has been through, and we'll
          only suggest products within your tolerance.
        </p>
      </div>

      <Card className="p-4 space-y-4">
        <div>
          <p className="text-sm font-medium text-gray-200">Skin type</p>
          <p className="text-xs text-gray-500 mb-2">
            {initial?.skin_type_source === "scan" && initial.skin_type
              ? `Your YouCam scan detected ${initial.skin_type} skin. Pick one only to override it.`
              : "Not sure? Skip it, and your YouCam scan will detect it from oiliness, moisture and redness."}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {SKIN_TYPES.map((t) => (
              <Chip key={t} active={skinType === t} onClick={() => setSkinType(skinType === t ? null : t)}>
                <span className="capitalize">{t}</span>
              </Chip>
            ))}
          </div>
        </div>
        <div>
          <p className="text-sm font-medium text-gray-200 mb-2">What do you want to work on?</p>
          <div className="flex flex-wrap gap-1.5">
            {CONCERNS.map((c) => (
              <Chip key={c.id} active={concerns.includes(c.id)} onClick={() => toggle(concerns, setConcerns, c.id)}>
                {c.label}
              </Chip>
            ))}
          </div>
        </div>
        <div>
          <p className="text-sm font-medium text-gray-200 mb-2">Ingredients your skin reacts to</p>
          <div className="flex flex-wrap gap-1.5">
            {(catalog?.sensitizers ?? []).map((s) => (
              <Chip key={s.id} active={sensitizers.includes(s.id)} onClick={() => toggle(sensitizers, setSensitizers, s.id)}>
                {s.label}
              </Chip>
            ))}
          </div>
        </div>
      </Card>

      {catalog && (
        <Card className="p-4 space-y-5">
          <ProductPicker
            label="Products that burned, stung or peeled your skin"
            hint="We'll never suggest anything that strong again."
            products={catalog.products}
            selected={burned}
            onChange={setBurned}
          />
          <ProductPicker
            label="Actives you've used happily for a month or more"
            hint="Proves your tolerance, so we can suggest the next careful step."
            products={catalog.products}
            selected={worked}
            onChange={setWorked}
          />
        </Card>
      )}

      <Card className="p-4">
        <p className="text-sm font-medium text-gray-200">Your shopping style</p>
        <p className="text-xs text-gray-500 mb-2">
          Only used to break ties between equally honest options. It never outranks what actually works for your skin.
        </p>
        <div className="flex flex-wrap gap-1.5">
          {(catalog?.styles ?? []).map((s) => (
            <Chip key={s} active={styles.includes(s)} onClick={() => toggle(styles, setStyles, s)}>
              <span className="capitalize">{s}</span>
            </Chip>
          ))}
        </div>
      </Card>

      {error && <p role="alert" className="text-sm text-rose-400">{error}</p>}
      <div className="flex gap-2 justify-end pb-6">
        {onCancel && (
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button onClick={handleSubmit} disabled={saving}>
          {saving ? "Saving…" : "Show my honest picks"}
        </Button>
      </div>
    </div>
  );
};

export default OnboardingScreen;
