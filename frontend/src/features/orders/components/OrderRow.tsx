import { Bed, Building2, Server } from "lucide-react";
import { formatDateTime, formatElapsed, formatPatientName } from "../../../lib/formatters";
import { useNow } from "../../../hooks/useNow";
import type { MedicalOrderRead } from "../types/order.types";
import OrderActions from "./OrderActions";
import ModalityBadge from "./ModalityBadge";
import PriorityBadge from "./PriorityBadge";
import StateBadge from "./StateBadge";

const WARN_AFTER_MIN = 60;
const CRITICAL_AFTER_MIN = 120;

function elapsedMinutes(
  createdAt: string | null | undefined,
  now: number,
): number {
  if (!createdAt) return 0;
  return Math.max(
    0,
    Math.floor((now - new Date(createdAt).getTime()) / 60_000),
  );
}

interface OrderRowProps {
  order: MedicalOrderRead;
}

export default function OrderRow({ order }: OrderRowProps) {
  const now = useNow();
  const minutes = elapsedMinutes(order.created_at, now);
  const elapsedClass =
    minutes >= CRITICAL_AFTER_MIN
      ? "bg-red-100 text-red-700"
      : minutes >= WARN_AFTER_MIN
        ? "bg-amber-100 text-amber-700"
        : "bg-gray-100 text-gray-500";

  return (
    <tr className="border-b border-gray-100 transition-colors hover:bg-blue-200 even:bg-blue-100">
      <td className="whitespace-nowrap px-4 py-4 text-sm text-gray-500">
        <div>{formatDateTime(order.created_at)}</div>
        <span
          className={`mt-0.5 inline-flex items-center rounded px-1.5 py-0.5 text-[11px] font-medium ${elapsedClass}`}
        >
          {formatElapsed(order.created_at, now)}
        </span>
      </td>
      <td className="px-4 py-4">
        <div className="text-sm font-semibold text-gray-900">
          {formatPatientName(order.patient.lastname, order.patient.name)}
        </div>
        <div className="whitespace-nowrap font-mono text-xs text-gray-500">
          DNI {Number(order.patient.dni).toLocaleString("ES-AR")}
        </div>
      </td>
      <td className="px-4 py-4">
        <div className="flex flex-col items-center gap-0.5">
          <PriorityBadge priority={order.order.triage_priority} />
          <StateBadge state={order.order.state} size="xs" />
        </div>
      </td>
      <td className="px-4 py-4 text-sm text-gray-700">
        <div
          className="max-w-60"
          title={`${order.order.modality} · ${order.order.description}`}
        >
          {order.order.description}
        </div>
        <div className="mt-0.5">
          <ModalityBadge modality={order.order.modality} size="md" />
        </div>
      </td>
      <td className="px-4 py-4 text-sm text-gray-500">
        <div>{order.order.location}</div>
        <div className="mt-0.5 flex flex-wrap items-center gap-1">
          <span className="inline-flex items-center gap-1 rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-500">
            <Server size={11} />
            {order.source_system}
          </span>
          <span className="inline-flex items-center gap-1 rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-500">
            {order.order.study_setting === "En Cama" ? (
              <Bed size={11} />
            ) : (
              <Building2 size={11} />
            )}
            {order.order.study_setting}
          </span>
        </div>
      </td>
      <td className="px-4 py-4">
        <div className="flex flex-col items-start gap-1">
          <OrderActions order={order} compact vertical showRetriage={false} />
        </div>
      </td>
    </tr>
  );
}
