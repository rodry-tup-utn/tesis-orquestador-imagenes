import Badge from "../../../components/ui/Badge";

interface NotificationStatusBadgeProps {
  status: string;
}

const STATUS_VARIANTS: Record<string, "green" | "red" | "amber" | "neutral"> = {
  SUCCESS: "green",
  FAILED: "red",
  PENDING: "amber",
};

export default function NotificationStatusBadge({
  status,
}: NotificationStatusBadgeProps) {
  return (
    <Badge variant={STATUS_VARIANTS[status] ?? "neutral"}>
      {status}
    </Badge>
  );
}
