import { motion, useReducedMotion, type Variants } from "framer-motion";
import {
  ArrowRight,
  Camera,
  CheckCircle2,
  ClipboardList,
  Leaf,
  MessageCircle,
  MessageSquare,
  Scan,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Volume2,
} from "lucide-react";
import Blob from "./ui/Blob";
import Button from "./ui/Button";
import Card from "./ui/Card";
import SectionHeading from "./ui/SectionHeading";

interface LandingScreenProps {
  onStartScan: () => void;
  onAskWabi: () => void;
}

const WHY_ITEMS = [
  {
    icon: CheckCircle2,
    title: "Grounded advice",
    description: "Every suggestion traces back to a measured score — never a guess dressed up as fact.",
  },
  {
    icon: ShieldCheck,
    title: "Visible confidence",
    description: "You always see how sure Wabi is, spoken aloud alongside the advice, never hidden.",
  },
  {
    icon: Volume2,
    title: "Voice-first",
    description: "Full results, spoken — usable with the screen off, start to finish.",
  },
];

const HOW_STEPS = [
  {
    icon: Camera,
    title: "Scan",
    description: "Take a photo. Real skin metrics come back — moisture, texture, redness, and more.",
  },
  {
    icon: Scan,
    title: "Grounding check",
    description: "Every piece of advice is checked against your actual scores before it's said out loud.",
  },
  {
    icon: Volume2,
    title: "Spoken result",
    description: "You hear your results, the advice, and exactly how confident Wabi is — together.",
  },
];

const FEATURES = [
  {
    icon: ClipboardList,
    title: "Personalised routine",
    description: "Advice organised by what your skin actually measured.",
  },
  {
    icon: TrendingUp,
    title: "Progress over time",
    description: "Scan again later and see what's genuinely changed.",
  },
  {
    icon: MessageSquare,
    title: "Talk it through",
    description: "Take any scan straight into a conversation with Wabi.",
  },
  {
    icon: Leaf,
    title: "Plain-language guidance",
    description: "Ingredient categories explained simply, no jargon.",
  },
];

const sectionVariant: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: i * 0.08, ease: [0.25, 0.1, 0.25, 1] as const },
  }),
};

const LandingScreen: React.FC<LandingScreenProps> = ({ onStartScan, onAskWabi }) => {
  const shouldReduceMotion = useReducedMotion();
  const stagger = (i: number) => (shouldReduceMotion ? 0 : i);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="h-full overflow-y-auto bg-ink snap-y snap-proximity"
    >
      {/* Hero */}
      <section className="relative overflow-hidden px-6 py-16 min-h-screen flex flex-col items-center justify-center text-center gap-6 snap-start">
        <Blob className="w-72 h-72 -top-10 -left-10" color="bg-brand-500/20" />
        <Blob className="w-64 h-64 top-20 right-0" color="bg-lavender/15" />
        <Blob className="w-56 h-56 bottom-0 left-1/3" color="bg-coral/15" />

        <div className="relative z-10 flex flex-col items-center gap-8 max-w-4xl">
          <div className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white/5 backdrop-blur-md border border-white/10 shadow-glass">
            <Sparkles size={16} className="text-brand-400" aria-hidden="true" />
            <span className="text-sm font-semibold uppercase tracking-wider text-gray-300">Honest skincare · powered by YouCam Skin AI</span>
          </div>

          <span className="text-2xl font-display font-semibold tracking-wide text-gray-100">Wabi · Sabi</span>

          <h1 className="text-5xl md:text-7xl font-display font-semibold leading-tight bg-gradient-to-br from-white via-brand-400 to-lavender bg-clip-text text-transparent">
            Skincare that works for you, not the hype.
          </h1>

          <p className="text-xl md:text-2xl text-gray-400 max-w-2xl">
            Take a photo. YouCam measures 11 skin concerns, Wabi-Sabi learns what your skin can tolerate, and
            recommends only products that actually help you, flagging the overpriced and the overhyped.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4">
            <Button variant="primary" size="lg" icon={Camera} onClick={onStartScan}>
              Start Scan
            </Button>
            <Button variant="secondary" size="lg" icon={MessageCircle} onClick={onAskWabi}>
              Ask Wabi a question
            </Button>
          </div>

          <p className="flex items-center gap-1.5 text-sm text-gray-500">
            <ShieldCheck size={16} aria-hidden="true" />
            No account required — sign in only if you want your history synced.
          </p>
        </div>
      </section>

      {/* Why this matters */}
      <section className="relative px-6 py-16 min-h-screen flex flex-col items-center justify-center bg-white/[0.02] snap-start">
        <SectionHeading
          eyebrow="Why it's different"
          title="Advice you can actually check"
          subtitle="Most AI skincare chat just sounds confident. Wabi-Sabi is built so you can see whether it's earned."
          className="mb-14 mx-auto"
        />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {WHY_ITEMS.map((item, i) => (
            <motion.div
              key={item.title}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-60px" }}
              custom={stagger(i)}
              variants={sectionVariant}
            >
              <Card variant="glass" hover className="p-8 h-full flex flex-col gap-4">
                <div className="w-14 h-14 rounded-full bg-brand-500/10 flex items-center justify-center">
                  <item.icon size={26} className="text-brand-400" aria-hidden="true" />
                </div>
                <h3 className="text-xl font-semibold text-gray-100">{item.title}</h3>
                <p className="text-base text-gray-400">{item.description}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="relative px-6 py-16 min-h-screen flex flex-col items-center justify-center snap-start">
        <SectionHeading eyebrow="How it works" title="Three steps, spoken end to end" className="mb-14 mx-auto" />
        <div className="flex flex-col md:flex-row items-stretch justify-center gap-6 max-w-6xl mx-auto">
          {HOW_STEPS.map((step, i) => (
            <motion.div
              key={step.title}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-60px" }}
              custom={stagger(i)}
              variants={sectionVariant}
              className="flex items-center gap-6 flex-1"
            >
              <Card variant="solid" className="p-8 flex-1 flex flex-col gap-4">
                <div className="flex items-center gap-3">
                  <span className="w-10 h-10 rounded-full bg-brand-500 text-white text-sm font-semibold flex items-center justify-center">
                    {i + 1}
                  </span>
                  <step.icon size={24} className="text-brand-400" aria-hidden="true" />
                </div>
                <h3 className="text-xl font-semibold text-gray-100">{step.title}</h3>
                <p className="text-base text-gray-400">{step.description}</p>
              </Card>
              {i < HOW_STEPS.length - 1 && (
                <ArrowRight size={28} className="hidden md:block text-gray-700 flex-shrink-0" aria-hidden="true" />
              )}
            </motion.div>
          ))}
        </div>
      </section>

      {/* What you get */}
      <section className="relative px-6 py-16 min-h-screen flex flex-col items-center justify-center bg-white/[0.02] snap-start">
        <SectionHeading eyebrow="What you get" title="Beyond a single scan" className="mb-14 mx-auto" />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-5xl mx-auto">
          {FEATURES.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-60px" }}
              custom={stagger(i)}
              variants={sectionVariant}
            >
              <Card variant="glass" hover className="p-8 h-full flex items-start gap-5">
                <div className="w-14 h-14 rounded-full bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                  <feature.icon size={24} className="text-brand-400" aria-hidden="true" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-100">{feature.title}</h3>
                  <p className="text-base text-gray-400">{feature.description}</p>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative px-6 py-16 min-h-screen flex flex-col items-center justify-center text-center gap-4 overflow-hidden snap-start">
        <Blob className="w-64 h-64 -bottom-16 right-0" color="bg-brand-500/15" />
        <Blob className="w-56 h-56 top-10 -left-10" color="bg-lavender/10" />
        <h2 className="relative z-10 text-4xl md:text-6xl font-display font-semibold text-gray-100 max-w-3xl">
          Ready to see what your skin actually needs?
        </h2>
        <p className="relative z-10 text-lg md:text-xl text-gray-400 max-w-xl">
          One photo. Real measurements. Advice you can check.
        </p>
        <div className="relative z-10">
          <Button variant="primary" size="lg" icon={Camera} onClick={onStartScan}>
            Start Scan
          </Button>
        </div>
      </section>
    </motion.div>
  );
};

export default LandingScreen;
