import { useState } from "react";
import ErrorState from "../../../components/ui/ErrorState";
import Pagination from "../../../components/ui/Pagination";
import { useNotifications } from "../hooks/useNotifications";
import NotificationsTable from "../components/NotificationsTable";
import NotificationPayloadModal, {
  usePayloadModal,
} from "../components/NotificationPayloadModal";

const PAGE_SIZE = 20;

export default function NotificationsPage() {
  const [page, setPage] = useState(0);
  const { open, close, payload } = usePayloadModal();

  const offset = page * PAGE_SIZE;
  const { data, isPending, isFetching, isError, error, refetch } =
    useNotifications(offset, PAGE_SIZE);

  const notifications = data ?? [];
  const hasNext = notifications.length === PAGE_SIZE;
  const totalPages = page + (hasNext ? 2 : 1);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Notificaciones</h1>
        <p className="text-sm text-gray-500">
          Alertas emitidas hacia n8n / Telegram
        </p>
      </div>

      {isError && (
        <ErrorState
          message={error?.message ?? "Error al cargar las notificaciones"}
          onRetry={() => void refetch()}
        />
      )}

      <NotificationsTable
        notifications={notifications}
        loading={isPending}
        onSelect={(n) => open(n.payload_sent)}
      />

      <Pagination
        page={page}
        totalPages={totalPages}
        loading={isFetching}
        onPageChange={setPage}
      />

      <NotificationPayloadModal
        open={payload != null}
        payload={payload ?? ""}
        onClose={close}
      />
    </div>
  );
}
