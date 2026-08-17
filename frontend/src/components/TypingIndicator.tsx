import { motion, useReducedMotion } from "framer-motion";

const TypingIndicator: React.FC = () => {
  const shouldReduceMotion = useReducedMotion();

  const bounce = (delay: number) =>
    shouldReduceMotion
      ? {}
      : {
          animate: { y: [0, -4, 0] },
          transition: { duration: 0.8, repeat: Infinity, ease: "easeInOut" as const, delay },
        };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex items-center space-x-1 p-3 bg-ink-card rounded-2xl rounded-bl-none shadow-soft"
    >
      <motion.div {...bounce(0)} className="w-2 h-2 bg-gray-500 rounded-full" />
      <motion.div {...bounce(0.2)} className="w-2 h-2 bg-gray-500 rounded-full" />
      <motion.div {...bounce(0.4)} className="w-2 h-2 bg-gray-500 rounded-full" />
    </motion.div>
  );
};

export default TypingIndicator;
