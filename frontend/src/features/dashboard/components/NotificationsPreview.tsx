import { Link } from "react-router-dom";
import Card from "../../../components/ui/Card";
import { formatDateTime } from "../../../lib/formatters";
import NotificationStatusBadge from "../../notifications/components/NotificationStatusBadge";
import type { Notification } from "../../notifications/types/notification.types";

interface NotificationsPreviewProps {
  notifications: Notification[];
  loading: boolean;
}

export default function NotificationsPreview({
  notifications,
  loading,
}: NotificationsPreviewProps) {
  return (
    <Card
      title="Últimas notificaciones"
      subtitle="Alertas emitidas hacia n8n / Telegram"
      actions={
        <Link
          to="/notifications"
          className="text-xs font-medium text-sky-600 hover:underline"
        >
          Ver todas →
        </Link>
      }
    >
      {loading ? (
        <div className="space-y-2 p-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-5 animate-pulse rounded bg-gray-200" />
          ))}
        </div>
      ) : notifications.length === 0 ? (
        <p className="px-4 py-8 text-center text-sm text-gray-500">
          No hay notificaciones emitidas todavía.
        </p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {notifications.map((notification) => (
            <li key={notification.id} className="flex items-center justify-between gap-3 px-4 py-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-gray-900">
                  {notification.patient_lastname}
                  {notification.patient_name ? `, ${notification.patient_name}` : ""}
                </p>
                <p className="text-xs text-gray-500">
                  Orden #{notification.medical_order_id} ·{" "}
                  {formatDateTime(notification.sent_at)}
                </p>
              </div>
              <NotificationStatusBadge status={notification.status} />
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
