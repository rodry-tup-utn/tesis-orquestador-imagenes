import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant =
  | "primary"
  | "secondary"
  | "danger"
  | "ghost"
  | "soft-primary"
  | "soft-danger"
  | "soft-warning"
  | "soft-success"
  | "soft-neutral";
type Size = "xs" | "sm" | "md";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
  iconOnly?: boolean;
}

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    "bg-sky-600 text-white hover:bg-sky-700 disabled:opacity-50 focus-visible:ring-sky-400/60",
  secondary:
    "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 focus-visible:ring-sky-400/60",
  danger:
    "bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 focus-visible:ring-red-400/60",
  ghost:
    "text-gray-600 hover:bg-gray-100 hover:text-gray-900 disabled:opacity-50 focus-visible:ring-sky-400/60",
  "soft-primary":
    "bg-sky-50 text-sky-700 hover:bg-sky-100 disabled:opacity-50 focus-visible:ring-sky-400/60",
  "soft-danger":
    "bg-red-50 text-red-700 hover:bg-red-100 disabled:opacity-50 focus-visible:ring-red-400/60",
  "soft-warning":
    "bg-amber-50 text-amber-700 hover:bg-amber-100 disabled:opacity-50 focus-visible:ring-amber-400/60",
  "soft-success":
    "bg-emerald-50 text-emerald-700 hover:bg-emerald-100 disabled:opacity-50 focus-visible:ring-emerald-400/60",
  "soft-neutral":
    "bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 focus-visible:ring-sky-400/60",
};

const SIZE_CLASSES: Record<Size, string> = {
  xs: "px-1.5 py-1 text-xs",
  sm: "px-2.5 py-1.5 text-xs",
  md: "px-3 py-2 text-sm",
};

const ICON_ONLY_SIZE: Record<Size, string> = {
  xs: "p-1.5",
  sm: "p-2",
  md: "p-2.5",
};

export default function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  iconOnly = false,
  className = "",
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 hover:cursor-pointer active:opacity-80 disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]} ${
        iconOnly ? ICON_ONLY_SIZE[size] : SIZE_CLASSES[size]
      } ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : (
        icon
      )}
      {children}
    </button>
  );
}
