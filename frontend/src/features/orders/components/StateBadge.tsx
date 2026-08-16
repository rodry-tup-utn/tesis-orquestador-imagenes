import Badge from "../../../components/ui/Badge";
import type { OrderState } from "../types/order.types";

interface StateBadgeProps {
  state: OrderState;
  size?: "xs" | "sm" | "md";
}

const STATE_VARIANTS: Record<
  OrderState,
  "blue" | "cyan" | "green" | "neutral"
> = {
  Pendiente: "blue",
  "En Proceso": "cyan",
  Finalizada: "green",
  Cancelada: "neutral",
};

export default function StateBadge({ state, size }: StateBadgeProps) {
  return <Badge variant={STATE_VARIANTS[state]} size={size}>{state}</Badge>;
}
