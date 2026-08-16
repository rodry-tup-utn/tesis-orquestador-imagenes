import Badge from "../../../components/ui/Badge";

interface OrderNotificationBadgeProps {
  notified: boolean;
}

export default function OrderNotificationBadge({
  notified,
}: OrderNotificationBadgeProps) {
  return (
    <Badge
      variant={notified ? "green" : "neutral"}
      dot
      title={notified ? "Orden notificada por Telegram" : "Pendiente de notificación"}
    >
      {notified ? "Notificada" : "No notificada"}
    </Badge>
  );
}
