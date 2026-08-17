import type { HTMLAttributes } from "react";

type CardVariant = "solid" | "glass";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  hover?: boolean;
}

const VARIANT_CLASSES: Record<CardVariant, string> = {
  solid: "bg-ink-card border border-white/5 shadow-soft",
  glass: "bg-white/5 backdrop-blur-md border border-white/10 shadow-glass",
};

const Card: React.FC<CardProps> = ({ variant = "solid", hover = false, className = "", children, ...rest }) => {
  const hoverClasses = hover
    ? "transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lift"
    : "";

  return (
    <div className={`rounded-2xl ${VARIANT_CLASSES[variant]} ${hoverClasses} ${className}`} {...rest}>
      {children}
    </div>
  );
};

export default Card;
