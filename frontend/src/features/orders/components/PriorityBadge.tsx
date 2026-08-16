import Badge from "../../../components/ui/Badge";
import type { MedicalPriority } from "../types/order.types";

interface PriorityBadgeProps {
  priority: MedicalPriority;
  size?: "xs" | "sm" | "md";
}

const PRIORITY_VARIANTS: Record<
  MedicalPriority,
  "red" | "orange" | "amber" | "green"
> = {
  Crítico: "red",
  Urgente: "orange",
  Prioritario: "amber",
  Rutina: "green",
};

export default function PriorityBadge({
  priority,
  size,
}: PriorityBadgeProps) {
  return <Badge variant={PRIORITY_VARIANTS[priority]} size={size}>{priority}</Badge>;
}
