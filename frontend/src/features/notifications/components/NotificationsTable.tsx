import type { Notification } from "../types/notification.types";
import NotificationStatusBadge from "./NotificationStatusBadge";

interface NotificationsTableProps {
  notifications: Notification[];
  loading: boolean;
  onSelect: (notification: Notification) => void;
}

export default function NotificationsTable({
  notifications,
  loading,
  onSelect,
}: NotificationsTableProps) {
  if (loading && notifications.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-5 animate-pulse rounded bg-gray-200" />
        ))}
      </div>
    );
  }

  if (notifications.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white px-4 py-12 text-center text-sm text-gray-500 shadow-sm">
        No hay notificaciones emitidas todavía.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Orden</th>
              <th className="px-4 py-3">Paciente</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Enviada</th>
              <th className="px-4 py-3">Hash seudónimo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {notifications.map((notification) => (
              <tr
                key={notification.id}
                onClick={() => onSelect(notification)}
                className="cursor-pointer hover:bg-gray-50"
              >
                <td className="px-4 py-3 text-sm text-gray-500">
                  {notification.id}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-gray-600">
                  #{notification.medical_order_id}
                </td>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {notification.patient_lastname}
                  {notification.patient_name
                    ? `, ${notification.patient_name}`
                    : ""}
                </td>
                <td className="px-4 py-3">
                  <NotificationStatusBadge status={notification.status} />
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {new Date(notification.sent_at).toLocaleString("es-AR", {
                    dateStyle: "short",
                    timeStyle: "short",
                  })}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-gray-400">
                  {notification.pseudonym_hash.slice(0, 16)}…
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
