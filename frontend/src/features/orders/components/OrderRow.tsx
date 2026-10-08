import { Bed, Building2, MapPin, Server } from "lucide-react";
import {
  formatDate,
  formatElapsed,
  formatPatientName,
  formatTime,
  splitLocation,
} from "../../../lib/formatters";
import { useNow } from "../../../hooks/useNow";
import type { MedicalOrderRead } from "../types/order.types";
import OrderActions from "./OrderActions";
import ModalityBadge from "./ModalityBadge";
import PriorityBadge from "./PriorityBadge";
import StateBadge from "./StateBadge";

const WARN_AFTER_MIN = 60;
const CRITICAL_AFTER_MIN = 120;

const SOURCE_SYSTEM_CLASSES: Record<string, string> = {
  AMBULATORIO: "bg-sky-100 text-sky-700",
  GUARDIA: "bg-red-100 text-red-700",
  INTERNACION: "bg-violet-100 text-violet-700",
};

const SETTING_CLASSES = {
  cama: "bg-orange-100 text-orange-700",
  efector: "bg-green-100 text-green-700",
} as const;

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

  const locValue = order.order.location?.trim() ?? "";
  const showLocation = order.source_system !== "AMBULATORIO" && locValue !== "";
  const location = splitLocation(locValue);

  return (
    <tr className="border-b border-gray-100 text-center transition-colors hover:bg-blue-200 even:bg-blue-100">
      <td className="whitespace-nowrap px-4 py-4 text-sm text-gray-500 text-center">
        <div className="text-base font-medium text-gray-700">
          {formatDate(order.created_at)}
        </div>
        <div className="text-gray-500">{formatTime(order.created_at)}</div>
        <span
          className={`mt-0.5 inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${elapsedClass}`}
        >
          {`Hace ${formatElapsed(order.created_at, now)}`}
        </span>
      </td>
      <td className="px-4 py-4">
        <div className="text-lg font-semibold text-gray-900">
          {formatPatientName(order.patient.lastname, order.patient.name)}
        </div>
        <div className="whitespace-nowrap font-mono text-sm text-gray-500">
          DNI {Number(order.patient.dni).toLocaleString("ES-AR")}
        </div>
      </td>
      <td className="px-4 py-4">
        <div className="flex flex-col gap-0.5">
          <PriorityBadge priority={order.order.triage_priority} size="lg" />
          <StateBadge state={order.order.state} size="lg" />
        </div>
      </td>
      <td className="px-4 py-4 text-sm text-center text-gray-700">
        <div className="mb-2 flex flex-col">
          <ModalityBadge modality={order.order.modality} size="lg" />
        </div>
        <div
          className="max-w-60 text-base"
          title={`${order.order.modality} · ${order.order.description}`}
        >
          {order.order.description}
        </div>
      </td>
      <td className="px-4 py-4 text-sm text-gray-500">
        <span
          className={`inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-sm font-medium ${SOURCE_SYSTEM_CLASSES[order.source_system] ?? "bg-gray-100 text-gray-500"}`}
        >
          <Server size={16} />
          {order.source_system}
        </span>
        <div className="mt-1.5 flex flex-col items-center gap-1 rounded-md bg-gray-100 p-1.5">
          {showLocation && (
            <div className="flex w-full items-start justify-center gap-1.5">
              <MapPin size={16} className="mt-0.5 shrink-0 text-green-600" />
              <div className="min-w-0">
                <div
                  className="truncate text-base font-semibold text-gray-900"
                  title={locValue}
                >
                  {location.main}
                </div>
                {location.rest && (
                  <div
                    className="truncate font-mono text-sm text-gray-500"
                    title={locValue}
                  >
                    {location.rest}
                  </div>
                )}
              </div>
            </div>
          )}
          <span
            className={`inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-sm font-medium uppercase ${order.order.study_setting === "En Cama" ? SETTING_CLASSES.cama : SETTING_CLASSES.efector}`}
          >
            {order.order.study_setting === "En Cama" ? (
              <Bed size={16} />
            ) : (
              <Building2 size={16} />
            )}
            {order.order.study_setting}
          </span>
        </div>
      </td>
      <td className="px-4 py-4">
        <OrderActions order={order} size="md" vertical showRetriage={false} />
      </td>
    </tr>
  );
}
