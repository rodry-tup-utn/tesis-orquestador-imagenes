import type { LucideIcon } from "lucide-react";
import { CircleCheck, CircleX, Hourglass, Loader } from "lucide-react";
import Badge from "../../../components/ui/Badge";
import type { OrderState } from "../types/order.types";

interface StateBadgeProps {
  state: OrderState;
  size?: "xs" | "sm" | "md" | "lg";
}

const STATE_VARIANTS: Record<
  OrderState,
  "amber" | "cyan" | "violet" | "neutral"
> = {
  Pendiente: "amber",
  "En Proceso": "cyan",
  Finalizada: "violet",
  Cancelada: "neutral",
};

const STATE_ICONS: Record<OrderState, LucideIcon> = {
  Pendiente: Hourglass,
  "En Proceso": Loader,
  Finalizada: CircleCheck,
  Cancelada: CircleX,
};

const ICON_SIZES: Record<"xs" | "sm" | "md" | "lg", number> = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 16,
};

export default function StateBadge({ state, size = "md" }: StateBadgeProps) {
  const Icon = STATE_ICONS[state];
  return (
    <Badge
      variant={STATE_VARIANTS[state]}
      size={size}
      icon={<Icon size={ICON_SIZES[size]} />}
    >
      {state}
    </Badge>
  );
}
