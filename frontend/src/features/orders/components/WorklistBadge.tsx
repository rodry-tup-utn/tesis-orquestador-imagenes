import Badge from "../../../components/ui/Badge";

interface WorklistBadgeProps {
  sent: boolean;
}

export default function WorklistBadge({ sent }: WorklistBadgeProps) {
  return (
    <Badge
      variant={sent ? "green" : "neutral"}
      dot
      title={sent ? "Worklist enviada" : "Pendiente de envío a Worklist"}
    >
      {sent ? "Enviada" : "Pendiente"}
    </Badge>
  );
}
