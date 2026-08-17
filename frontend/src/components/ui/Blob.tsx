interface BlobProps {
  className?: string;
  color?: string;
}

// Purely decorative background shape — never intercepts clicks or reaches
// screen readers. Its drift animation is a raw CSS @keyframes (see
// tailwind.config.js `animate-blob`), not framer-motion, so the
// prefers-reduced-motion override lives in index.css rather than a
// useReducedMotion() check here.
const Blob: React.FC<BlobProps> = ({ className = "", color = "bg-brand-500/20" }) => (
  <div aria-hidden="true" className={`absolute rounded-full blur-3xl opacity-40 animate-blob pointer-events-none ${color} ${className}`} />
);

export default Blob;
