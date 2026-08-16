import Badge from "../../../components/ui/Badge";
import { MODALITY_LABELS } from "../../../lib/formatters";
import type { Modality } from "../types/order.types";

interface ModalityBadgeProps {
  modality: Modality;
  size?: "xs" | "sm" | "md";
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

export default function ModalityBadge({ modality, size }: ModalityBadgeProps) {
  return (
    <Badge variant={MODALITY_VARIANTS[modality]} size={size} dot uppercase>
      {MODALITY_LABELS[modality]}
    </Badge>
  );
}
