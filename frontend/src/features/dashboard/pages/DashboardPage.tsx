import { Link } from "react-router-dom";
import Card from "../../../components/ui/Card";
import ErrorState from "../../../components/ui/ErrorState";
import { MODALITY_LABELS } from "../../../lib/formatters";
import { MODALITIES } from "../../orders/constants/order.constants";
import {
  useDashboardStats,
  useLatestNotifications,
} from "../hooks/useDashboard";
import NotificationsPreview from "../components/NotificationsPreview";
import StatCard from "../components/StatCard";

const PRIORITY_ORDER = ["Crítico", "Urgente", "Prioritario", "Rutina"] as const;
const STATE_ORDER = [
  "Pendiente",
  "En Proceso",
  "Finalizada",
  "Cancelada",
] as const;

export default function DashboardPage() {
  const stats = useDashboardStats();
  const notifications = useLatestNotifications(5);

  const data = stats.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500">
          Resumen del estado actual del orquestador
        </p>
      </div>

      {stats.isError && (
        <ErrorState
          message={stats.error?.message ?? "Error al cargar las estadísticas"}
          onRetry={() => void stats.refetch()}
        />
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Órdenes totales" value={data?.total ?? "—"} />
        <StatCard
          label="Críticas pendientes"
          value={data?.critical_pending ?? "—"}
          accent="text-red-600"
        />
        <StatCard label="Notificadas" value={data?.notified ?? "—"} />
        <StatCard
          label="Última actividad"
          value={formatCompactDate(data?.latest_created_at)}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Por prioridad de triaje">
          <PriorityBreakdown data={data?.by_priority} />
        </Card>
        <Card title="Por estado">
          <StateBreakdown data={data?.by_state} />
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card
          title="Por modalidad"
          subtitle="Distribución de estudios"
          actions={
            <Link
              to="/orders"
              className="text-xs font-medium text-sky-600 hover:underline"
            >
              Ver todas →
            </Link>
          }
        >
          <ModalityBreakdown data={data?.by_modality} />
        </Card>
        <NotificationsPreview
          notifications={notifications.data ?? []}
          loading={notifications.isPending}
        />
      </div>
    </div>
  );
}

function formatCompactDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("es-AR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function PriorityBreakdown({
  data,
}: {
  data: Record<string, number> | undefined;
}) {
  const total = PRIORITY_ORDER.reduce(
    (sum, key) => sum + (data?.[key] ?? 0),
    0,
  );
  return (
    <BarList
      rows={PRIORITY_ORDER.map((key) => ({
        key,
        label: key,
        value: data?.[key] ?? 0,
        barClass:
          key === "Crítico"
            ? "bg-red-500"
            : key === "Urgente"
              ? "bg-orange-500"
              : key === "Prioritario"
                ? "bg-yellow-400"
                : "bg-green-300",
      }))}
      total={total}
    />
  );
}

function StateBreakdown({
  data,
}: {
  data: Record<string, number> | undefined;
}) {
  const total = STATE_ORDER.reduce((sum, key) => sum + (data?.[key] ?? 0), 0);
  return (
    <BarList
      rows={STATE_ORDER.map((key) => ({
        key,
        label: key,
        value: data?.[key] ?? 0,
        barClass:
          key === "Pendiente"
            ? "bg-blue-500"
            : key === "En Proceso"
              ? "bg-cyan-500"
              : key === "Finalizada"
                ? "bg-green-500"
                : "bg-gray-300",
      }))}
      total={total}
    />
  );
}

function ModalityBreakdown({
  data,
}: {
  data: Record<string, number> | undefined;
}) {
  const total = MODALITIES.reduce((sum, code) => sum + (data?.[code] ?? 0), 0);
  return (
    <BarList
      rows={MODALITIES.map((code) => ({
        key: code,
        label: `${code} · ${MODALITY_LABELS[code]}`,
        value: data?.[code] ?? 0,
        barClass: "bg-sky-500",
      }))}
      total={total}
    />
  );
}

function BarList({
  rows,
  total,
}: {
  rows: { key: string; label: string; value: number; barClass: string }[];
  total: number;
}) {
  return (
    <div className="space-y-3 p-4">
      {rows.map((row) => (
        <div key={row.key}>
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="text-gray-700">{row.label}</span>
            <span className="font-semibold text-gray-900">{row.value}</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
            <div
              className={`h-full rounded-full transition-all ${row.barClass}`}
              style={{
                width: total === 0 ? "0%" : `${(row.value / total) * 100}%`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
