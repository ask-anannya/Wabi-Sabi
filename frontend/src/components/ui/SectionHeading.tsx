interface SectionHeadingProps {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  align?: "left" | "center";
  className?: string;
}

const SectionHeading: React.FC<SectionHeadingProps> = ({
  eyebrow,
  title,
  subtitle,
  align = "center",
  className = "",
}) => (
  <div
    className={`flex flex-col gap-3 ${align === "center" ? "items-center text-center" : "items-start text-left"} ${className}`}
  >
    {eyebrow && (
      <span className="text-sm font-semibold uppercase tracking-wider text-brand-400">{eyebrow}</span>
    )}
    <h2 className="text-4xl md:text-6xl font-display font-semibold text-gray-100">{title}</h2>
    {subtitle && <p className="text-lg md:text-xl text-gray-400 max-w-2xl">{subtitle}</p>}
  </div>
);

export default SectionHeading;
