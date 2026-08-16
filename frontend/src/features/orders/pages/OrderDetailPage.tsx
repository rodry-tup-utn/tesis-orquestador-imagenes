import { Link, useParams } from "react-router-dom";
import type { ReactNode } from "react";
import {
  Activity,
  ArrowBigLeft,
  Bed,
  Bell,
  Building2,
  Cake,
  CalendarClock,
  ClipboardList,
  CreditCard,
  EyeOff,
  Fingerprint,
  HeartPulse,
  MapPin,
  MessageSquare,
  Notebook,
  Send,
  Server,
  Stethoscope,
  UserRound,
  Users,
} from "lucide-react";
import Spinner from "../../../components/ui/Spinner";
import ErrorState from "../../../components/ui/ErrorState";
import Card from "../../../components/ui/Card";
import {
  formatDateTime,
  formatDate,
  formatPatientName,
  capitalize,
} from "../../../lib/formatters";
import OrderActions from "../components/OrderActions";
import WorklistAction from "../components/WorklistAction";
import WorklistBadge from "../components/WorklistBadge";
import PriorityBadge from "../components/PriorityBadge";
import StateBadge from "../components/StateBadge";
import ModalityBadge from "../components/ModalityBadge";
import OrderNotificationBadge from "../components/OrderNotificationBadge";
import { useOrderQuery } from "../hooks/useOrdersQuery";
import { Sex } from "../types/order.types";

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const orderId = id ? Number(id) : null;

  const {
    data: order,
    isPending,
    isError,
    error,
    refetch,
  } = useOrderQuery(orderId);

  if (isPending) {
    return <Spinner />;
  }

  const buildGenre = (sex: Sex) => {
    if (sex == "FEMALE") return "Femenino";
    if (sex == "MALE") return "Masculino";
    return "Otro";
  };

  if (isError || !order) {
    return (
      <ErrorState
        message={error?.message ?? "No se pudo cargar la orden"}
        onRetry={() => void refetch()}
      />
    );
  }

  const patient = order.patient;
  const details = order.order;
  const isUrgentOriginal = details.original_priority === "URGENTE";
  const originalChip = (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
        isUrgentOriginal
          ? "bg-red-100 text-red-700"
          : "bg-gray-100 text-gray-600"
      }`}
    >
      {isUrgentOriginal ? "Urgente" : "Rutina"}
    </span>
  );

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div className="flex flex-col items-start justify-between gap-4 ">
        <div>
          <Link
            to="/orders"
            className="text-sm font-medium text-sky-600 hover:underline flex flex-row gap-4"
          >
            <ArrowBigLeft className="bg-blue-100 text-blue-700"></ArrowBigLeft>
            Volver a órdenes
          </Link>

          <h1 className="mt-1 text-xl font-semibold text-gray-900">
            Orden {order.external_id}
          </h1>
          <div className="mt-2">
            <span className="block text-[11px] font-semibold uppercase tracking-wide text-gray-400">
              Estado de la orden
            </span>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <PriorityBadge priority={details.triage_priority} />
              <StateBadge state={details.state} />
              <WorklistBadge sent={order.sent_to_orthanc} />
              <OrderNotificationBadge notified={order.was_notified} />
            </div>
          </div>
        </div>
        <div>
          <span className="block text-[11px] font-semibold uppercase tracking-wide text-gray-400">
            Acciones
          </span>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <OrderActions order={order} showDetailButton={false} />
          </div>
        </div>
      </div>

      <Card
        title="Datos del Paciente"
        icon={
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-sky-100 text-sky-700">
            <Notebook size={18} />
          </span>
        }
      >
        <div className="flex flex-wrap items-start justify-between gap-4 px-4 py-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-800">
                <UserRound size={20} />
              </span>
              <div>
                <span className="block text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                  Apellido y Nombre
                </span>
                <span className="block text-2xl font-bold tracking-tight text-gray-900">
                  {formatPatientName(patient.lastname, patient.name)}
                </span>
              </div>
            </div>

            <DetailRow
              label="DNI"
              icon={<CreditCard size={13} />}
              iconClass="bg-gray-100 text-gray-800"
              className="px-0 py-1"
            >
              {Number(patient.dni).toLocaleString("ES-AR")}
            </DetailRow>
          </div>
          <dl className="grid grid-cols-1 gap-x-10 gap-y-1 sm:grid-cols-2">
            <DetailRow
              label="Seudónimo"
              icon={<EyeOff size={13} />}
              iconClass="bg-violet-100 text-violet-700"
              className="px-0 py-1"
            >
              {patient.pseudonym}
            </DetailRow>
            <DetailRow
              label="Fecha de nacimiento"
              icon={<Cake size={13} />}
              iconClass="bg-amber-100 text-amber-700"
              className="px-0 py-1"
            >
              {formatDate(patient.dob)}
            </DetailRow>
            <DetailRow
              label="Sexo"
              icon={<Users size={13} />}
              iconClass="bg-cyan-100 text-cyan-700"
              className="px-0 py-1"
            >
              {buildGenre(patient.sex)}
            </DetailRow>
            <DetailRow
              label="Sistema"
              icon={<Activity size={13} />}
              iconClass="bg-red-100 text-red-800"
              className="px-0 py-1"
            >
              {capitalize(order.source_system)}
            </DetailRow>
          </dl>
        </div>
      </Card>

      <Card
        title="Orden médica"
        icon={
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-violet-100 text-violet-700">
            <ClipboardList size={18} />
          </span>
        }
      >
        <div className="px-4 py-4">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <CalendarClock size={15} className="text-orange-600" />
            Fecha de la orden:
            <span className="font-semibold text-gray-900">
              {formatDateTime(details.date)}
            </span>
          </div>

          <div className="mt-4">
            <p className="text-2xl indent-8 font-semibold leading-snug text-gray-900 py-6">
              {details.description}
            </p>
            <div className="mt-1.5">
              <ModalityBadge modality={details.modality} />
            </div>
          </div>

          <dl className="mt-4 grid gap-x-10 sm:grid-cols-2">
            <DetailRow
              label="Diagnóstico"
              icon={<HeartPulse size={13} />}
              iconClass="bg-red-100 text-red-700"
              className="px-0 py-1.5"
            >
              {details.diagnosis}
            </DetailRow>
            <DetailRow
              label="Ubicación"
              icon={<MapPin size={13} />}
              iconClass="bg-green-100 text-green-700"
              className="px-0 py-1.5"
            >
              {details.location}
            </DetailRow>
            <DetailRow
              label="Lugar de estudio"
              icon={
                details.study_setting === "En Cama" ? (
                  <Bed size={13} />
                ) : (
                  <Building2 size={13} />
                )
              }
              iconClass="bg-cyan-100 text-cyan-700"
              className="px-0 py-1.5"
            >
              {details.study_setting}
            </DetailRow>
            <DetailRow
              label="Observaciones"
              icon={<MessageSquare size={13} fill="currentColor" />}
              iconClass="bg-amber-100 text-amber-700"
              className="px-0 py-1.5"
            >
              {details.observations ?? "—"}
            </DetailRow>
          </dl>

          <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-gray-100 pt-3">
            <span className="flex items-center gap-2 text-sm text-gray-500">
              Estado: <StateBadge state={details.state} />
            </span>
            <span className="flex items-center gap-2 text-sm text-gray-500">
              Triaje: <PriorityBadge priority={details.triage_priority} />
            </span>
            <span className="flex items-center gap-2 text-sm text-gray-500">
              Original: {originalChip}
            </span>
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-gray-100 pt-3">
            <span className="flex items-center gap-2 text-sm text-gray-500">
              <Stethoscope size={15} className="text-amber-600" />
              Médico solicitante
            </span>
            <span className="font-medium text-gray-900">
              {details.requesting_physician}
            </span>
          </div>
        </div>
      </Card>

      <Card
        title="Integración PACS / Worklist"
        icon={
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-cyan-100 text-cyan-700">
            <Server size={18} />
          </span>
        }
      >
        <dl className="divide-y divide-gray-100 text-sm">
          <DetailRow
            label="Estado de envío"
            icon={<Send size={13} />}
            iconClass={
              order.sent_to_orthanc
                ? "bg-emerald-100 text-emerald-700"
                : "bg-gray-100 text-gray-500"
            }
          >
            {order.sent_to_orthanc ? "Worklist enviada" : "Pendiente de envío"}
          </DetailRow>
          <DetailRow
            label="Study Instance UID"
            icon={<Fingerprint size={13} />}
            iconClass="bg-gray-100 text-gray-500"
          >
            {order.study_instance_uid ?? "—"}
          </DetailRow>
          <DetailRow
            label="Notificación"
            icon={<Bell size={13} />}
            iconClass={
              order.was_notified
                ? "bg-green-100 text-green-700"
                : "bg-gray-100 text-gray-500"
            }
          >
            <OrderNotificationBadge notified={order.was_notified} />
          </DetailRow>
        </dl>
      </Card>
    </div>
  );
}

function DetailRow({
  label,
  icon,
  iconClass = "bg-gray-100 text-gray-500",
  className = "",
  children,
}: {
  label: string;
  icon?: ReactNode;
  iconClass?: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div className={`flex items-center gap-3 px-4 py-2.5 ${className}`}>
      {icon && (
        <span
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${iconClass}`}
        >
          {icon}
        </span>
      )}
      <div className="min-w-0 flex-1">
        <dt className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
          {label}
        </dt>
        <dd className="mt-0.5 break-words text-sm font-medium text-gray-900">
          {children}
        </dd>
      </div>
    </div>
  );
}
