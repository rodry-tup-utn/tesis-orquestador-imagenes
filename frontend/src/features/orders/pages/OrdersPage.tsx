import { useEffect, useMemo, useState } from "react";
import { Activity, CalendarClock, RefreshCw, Search, X } from "lucide-react";
import CountPill from "../../../components/ui/CountPill";
import ErrorState from "../../../components/ui/ErrorState";
import Pagination from "../../../components/ui/Pagination";
import Select from "../../../components/ui/Select";
import { useDashboardStats } from "../../dashboard/hooks/useDashboard";
import { MODALITY_LABELS } from "../../../lib/formatters";
import {
  MODALITIES,
  ORDER_STATES,
  PAGE_SIZE,
  SOURCE_SYSTEMS,
  STUDY_SETTINGS,
} from "../constants/order.constants";
import OrdersTable from "../components/OrdersTable";
import { useOrdersQuery } from "../hooks/useOrdersQuery";
import type {
  Modality,
  OrderFilters,
  OrderSetting,
  OrderState,
  SortBy,
  SortDir,
} from "../types/order.types";

const DEFAULT_SORT_DIR: Record<SortBy, SortDir> = {
  created_at: "desc",
  priority: "desc",
  patient_name: "asc",
};

export default function OrdersPage() {
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState<OrderFilters>({
    sort_by: "created_at",
    sort_dir: "desc",
  });
  const [search, setSearch] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => {
      const next = search.trim();
      if (next !== (filters.q ?? "")) {
        setPage(0);
        setFilters((prev) => ({ ...prev, q: next || undefined }));
      }
    }, 350);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  const queryFilters = useMemo<OrderFilters>(
    () => ({
      ...filters,
      offset: page * PAGE_SIZE,
      limit: PAGE_SIZE,
    }),
    [filters, page],
  );

  const { data, isPending, isFetching, isError, error, refetch } =
    useOrdersQuery(queryFilters);
  const statsQuery = useDashboardStats();

  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const handleSort = (field: SortBy) => {
    setPage(0);
    setFilters((prev) => {
      if (prev.sort_by === field) {
        return {
          ...prev,
          sort_dir: prev.sort_dir === "asc" ? "desc" : "asc",
        };
      }
      return { ...prev, sort_by: field, sort_dir: DEFAULT_SORT_DIR[field] };
    });
  };

  const set = (patch: Partial<OrderFilters>) => {
    setPage(0);
    setFilters((prev) => ({ ...prev, ...patch }));
  };

  const hasFilters =
    !!filters.q ||
    !!filters.start_date ||
    !!filters.end_date ||
    !!filters.order_state ||
    filters.was_notified !== undefined ||
    !!filters.modality ||
    !!filters.source_system ||
    !!filters.study_setting;

  const clear = () => {
    setSearch("");
    setPage(0);
    setFilters({ sort_by: filters.sort_by, sort_dir: filters.sort_dir });
  };

  const stats = statsQuery.data;
  const criticals = stats?.by_priority?.["Crítico"] ?? 0;
  const urgents = stats?.by_priority?.["Urgente"] ?? 0;

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-gray-200 bg-white shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 p-4">
          <div className="flex flex-wrap items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-100 text-sky-700">
              <Activity className="h-5 w-5" />
            </span>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                Órdenes médicas
              </h1>
              <p className="text-xs text-gray-500">
                {isFetching
                  ? "Actualizando…"
                  : `${total} orden(es) en el sistema`}
              </p>
            </div>
            <button
              type="button"
              onClick={() => void refetch()}
              title="Recargar"
              className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
            >
              <RefreshCw
                className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`}
              />
              Recargar
            </button>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <CountPill tipo="Total" valor={stats?.total ?? 0} />
            <CountPill tipo="Filtrados" valor={total} accent="gray" />
            <CountPill tipo="Críticos" valor={criticals} accent="red" />
            <CountPill tipo="Urgentes" valor={urgents} accent="orange" />
          </div>
        </div>

        <div className="space-y-3 p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative min-w-60 flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                className="w-full rounded-md border border-gray-300 py-2 pl-9 pr-3 text-sm placeholder:text-gray-400 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                placeholder="Paciente, DNI o ID externo…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <CalendarClock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  type="date"
                  title="Desde"
                  className="rounded-md border border-gray-300 py-2 pl-9 pr-3 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                  value={
                    filters.start_date ? filters.start_date.slice(0, 10) : ""
                  }
                  onChange={(e) =>
                    set({ start_date: e.target.value || undefined })
                  }
                />
              </div>
              <input
                type="date"
                title="Hasta"
                className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                value={filters.end_date ? filters.end_date.slice(0, 10) : ""}
                onChange={(e) => set({ end_date: e.target.value || undefined })}
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="w-44">
              <Select
                value={filters.order_state ?? ""}
                onChange={(e) =>
                  set({
                    order_state: (e.target.value || undefined) as
                      | OrderState
                      | undefined,
                  })
                }
              >
                <option value="">Todos los estados</option>
                {ORDER_STATES.map((state) => (
                  <option key={state} value={state}>
                    {state}
                  </option>
                ))}
              </Select>
            </div>
            <div className="w-44">
              <Select
                value={
                  filters.was_notified === undefined
                    ? ""
                    : String(filters.was_notified)
                }
                onChange={(e) => {
                  const v = e.target.value;
                  set({ was_notified: v === "" ? undefined : v === "true" });
                }}
              >
                <option value="">Notificación</option>
                <option value="true">Notificada</option>
                <option value="false">No notificada</option>
              </Select>
            </div>
            <div className="w-56">
              <Select
                value={filters.modality ?? ""}
                onChange={(e) =>
                  set({
                    modality: (e.target.value || undefined) as
                      | Modality
                      | undefined,
                  })
                }
              >
                <option value="">Todas las modalidades</option>
                {MODALITIES.map((modality) => (
                  <option key={modality} value={modality}>
                    {MODALITY_LABELS[modality]}
                  </option>
                ))}
              </Select>
            </div>
            <div className="w-44">
              <Select
                value={filters.source_system ?? ""}
                onChange={(e) =>
                  set({ source_system: e.target.value || undefined })
                }
              >
                <option value="">Todos los sistemas</option>
                {SOURCE_SYSTEMS.map((system) => (
                  <option key={system} value={system}>
                    {system}
                  </option>
                ))}
              </Select>
            </div>
            <div className="w-44">
              <Select
                value={filters.study_setting ?? ""}
                onChange={(e) =>
                  set({
                    study_setting: (e.target.value || undefined) as
                      | OrderSetting
                      | undefined,
                  })
                }
              >
                <option value="">Todos los lugares</option>
                {STUDY_SETTINGS.map((setting) => (
                  <option key={setting} value={setting}>
                    {setting}
                  </option>
                ))}
              </Select>
            </div>
            {hasFilters && (
              <button
                type="button"
                onClick={clear}
                title="Limpiar filtros"
                className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-2.5 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
              >
                <X className="h-4 w-4" /> Limpiar
              </button>
            )}
          </div>
        </div>
      </div>

      {isError && (
        <ErrorState
          message={error?.message ?? "Error al cargar las órdenes"}
          onRetry={() => void refetch()}
        />
      )}

      <OrdersTable
        orders={data?.items ?? []}
        loading={isPending}
        sortBy={filters.sort_by ?? "created_at"}
        sortDir={filters.sort_dir ?? "desc"}
        onSort={handleSort}
      />

      <Pagination
        page={page}
        totalPages={totalPages}
        loading={isFetching}
        onPageChange={setPage}
      />
    </div>
  );
}
