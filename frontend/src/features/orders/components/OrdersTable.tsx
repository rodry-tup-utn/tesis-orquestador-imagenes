import type { MedicalOrderRead, SortBy, SortDir } from "../types/order.types";
import OrderRow from "./OrderRow";
import OrdersEmptyState from "./OrdersEmptyState";
import OrdersTableSkeleton from "./OrdersTableSkeleton";
import SortHeader from "./SortHeader";

interface OrdersTableProps {
  orders: MedicalOrderRead[];
  loading: boolean;
  sortBy: SortBy;
  sortDir: SortDir;
  onSort: (field: SortBy) => void;
}

export default function OrdersTable({
  orders,
  loading,
  sortBy,
  sortDir,
  onSort,
}: OrdersTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-md">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-sky-900">
            <tr className="text-center text-xs font-semibold uppercase tracking-wide">
              <SortHeader
                label="Fecha"
                sortBy="created_at"
                active={sortBy}
                sortDir={sortDir}
                onSort={onSort}
                dark
              />
              <SortHeader
                label="Paciente"
                sortBy="patient_name"
                active={sortBy}
                sortDir={sortDir}
                onSort={onSort}
                dark
              />
              <SortHeader
                label="Prioridad / Estado"
                sortBy="priority"
                active={sortBy}
                sortDir={sortDir}
                onSort={onSort}
                dark
              />
              <th className="px-4 py-3 text-center text-white/80">Estudio</th>
              <th className="px-4 py-3 text-center text-white/80">Ubicación</th>
              <th className="px-4 py-3 text-center text-white/80">Acciones</th>
            </tr>
          </thead>
          {loading ? (
            <OrdersTableSkeleton />
          ) : orders.length === 0 ? (
            <OrdersEmptyState />
          ) : (
            <tbody className="divide-y divide-gray-100">
              {orders.map((order) => (
                <OrderRow key={order.id ?? order.external_id} order={order} />
              ))}
            </tbody>
          )}
        </table>
      </div>
    </div>
  );
}
