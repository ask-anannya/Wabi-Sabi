import type { ButtonHTMLAttributes, ElementType } from "react";

type ButtonVariant = "primary" | "secondary" | "dark";
type ButtonSize = "md" | "lg" | "icon";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: ElementType;
  trailingIcon?: ElementType;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-brand-500 text-white hover:bg-brand-600",
  secondary: "bg-white/10 backdrop-blur-sm text-gray-100 border border-white/15 hover:bg-white/20",
  // Inverted (light-on-dark) rather than literally black — a near-black
  // pill would nearly vanish against the app's dark ink background.
  dark: "bg-white text-ink hover:bg-gray-100",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  md: "px-5 py-2.5 text-sm gap-2",
  lg: "px-8 py-4 text-lg gap-2.5",
  icon: "w-11 h-11 p-0 justify-center",
};

const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  icon: Icon,
  trailingIcon: TrailingIcon,
  className = "",
  type = "button",
  children,
  ...rest
}) => {
  return (
    <button
      type={type}
      className={`group inline-flex items-center rounded-full font-medium shadow-soft transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-lift focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 focus-visible:ring-offset-ink disabled:opacity-50 disabled:pointer-events-none disabled:translate-y-0 disabled:shadow-soft ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`}
      {...rest}
    >
      {Icon && <Icon size={size === "icon" ? 18 : size === "lg" ? 20 : 16} aria-hidden="true" />}
      {children}
      {TrailingIcon && (
        <TrailingIcon
          size={size === "lg" ? 20 : 16}
          aria-hidden="true"
          className="transition-transform duration-300 group-hover:translate-x-1"
        />
      )}
    </button>
  );
};

export default Button;
