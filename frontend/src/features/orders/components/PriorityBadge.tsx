import type { LucideIcon } from "lucide-react";
import { ChevronUp, Minus, Siren, TriangleAlert } from "lucide-react";
import Badge from "../../../components/ui/Badge";
import type { MedicalPriority } from "../types/order.types";

interface PriorityBadgeProps {
  priority: MedicalPriority;
  size?: "xs" | "sm" | "md" | "lg";
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

const PRIORITY_ICONS: Record<MedicalPriority, LucideIcon> = {
  Crítico: Siren,
  Urgente: TriangleAlert,
  Prioritario: ChevronUp,
  Rutina: Minus,
};

const ICON_SIZES: Record<"xs" | "sm" | "md" | "lg", number> = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 16,
};

export default function PriorityBadge({ priority, size = "md" }: PriorityBadgeProps) {
  const Icon = PRIORITY_ICONS[priority];
  return (
    <Badge
      variant={PRIORITY_VARIANTS[priority]}
      size={size}
      icon={<Icon size={ICON_SIZES[size]} />}
    >
      {priority}
    </Badge>
  );
}
