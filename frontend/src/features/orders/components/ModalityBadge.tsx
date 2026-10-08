import type { LucideIcon } from "lucide-react";
import {
  Image,
  Scan,
  Magnet,
  Waves,
  Venus,
  Zap,
  FlaskConical,
  Crosshair,
} from "lucide-react";
import Badge from "../../../components/ui/Badge";
import { MODALITY_LABELS } from "../../../lib/formatters";
import type { Modality } from "../types/order.types";

interface ModalityBadgeProps {
  modality: Modality;
  size?: "xs" | "sm" | "md" | "lg";
}

const MODALITY_VARIANTS: Record<
  Modality,
  "blue" | "violet" | "green" | "red" | "pink" | "cyan" | "sky" | "orange"
> = {
  CT: "blue",
  MR: "violet",
  US: "green",
  DX: "red",
  MG: "pink",
  XA: "cyan",
  NM: "sky",
  PT: "orange",
};

const MODALITY_ICONS: Record<Modality, LucideIcon> = {
  DX: Image,
  CT: Scan,
  MR: Magnet,
  US: Waves,
  MG: Venus,
  XA: Zap,
  NM: FlaskConical,
  PT: Crosshair,
};

const ICON_SIZES: Record<"xs" | "sm" | "md" | "lg", number> = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 16,
};

export default function ModalityBadge({ modality, size = "md" }: ModalityBadgeProps) {
  const Icon = MODALITY_ICONS[modality];
  return (
    <Badge
      variant={MODALITY_VARIANTS[modality]}
      size={size}
      icon={<Icon size={ICON_SIZES[size]} />}
      uppercase
    >
      {MODALITY_LABELS[modality]}
    </Badge>
  );
}
