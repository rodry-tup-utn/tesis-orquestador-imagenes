import type { ReactNode } from "react";

type Variant =
  | "neutral"
  | "blue"
  | "cyan"
  | "sky"
  | "green"
  | "amber"
  | "orange"
  | "red"
  | "pink"
  | "violet";
type Size = "xs" | "sm" | "md";

interface BadgeProps {
  variant?: Variant;
  size?: Size;
  icon?: ReactNode;
  dot?: boolean;
  children: ReactNode;
  className?: string;
  title?: string;
  uppercase?: boolean;
}

const VARIANT_CLASSES: Record<Variant, string> = {
  neutral: "bg-gray-100 text-gray-600 ring-gray-600/20",
  blue: "bg-blue-100 text-blue-700 ring-blue-600/20",
  cyan: "bg-cyan-100 text-cyan-700 ring-cyan-600/20",
  sky: "bg-sky-100 text-sky-700 ring-sky-600/20",
  green: "bg-green-100 text-green-700 ring-green-600/20",
  amber: "bg-yellow-100 text-yellow-800 ring-yellow-600/20",
  orange: "bg-orange-100 text-orange-700 ring-orange-600/20",
  red: "bg-red-100 text-red-700 ring-red-600/20",
  pink: "bg-pink-100 text-pink-700 ring-pink-600/20",
  violet: "bg-violet-100 text-violet-700 ring-violet-600/20",
};

const SIZE_CLASSES: Record<Size, string> = {
  xs: "px-2 py-0.5 text-[11px]",
  sm: "px-2.5 py-0.5 text-xs",
  md: "px-3 py-1 text-xs",
};

export default function Badge({
  variant = "neutral",
  size = "md",
  icon,
  dot = false,
  children,
  className = "",
  title,
  uppercase = false,
}: BadgeProps) {
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full font-semibold ring-1 ring-inset ${uppercase ? "uppercase tracking-wide" : ""} ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`}
    >
      {dot && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-current" />}
      {icon}
      {children}
    </span>
  );
}
