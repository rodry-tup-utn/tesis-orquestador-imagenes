import type { Modality } from "../features/orders/types/order.types";

export const MODALITY_LABELS: Record<Modality, string> = {
  CT: "Tomografía",
  MR: "Resonancia Magnética",
  US: "Ecografía",
  DX: "Radiografía",
  MG: "Mamografía",
  XA: "Angiografía",
  NM: "Medicina Nuclear",
  PT: "PET",
};

export function capitalize(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return "";
  return trimmed.charAt(0).toUpperCase() + trimmed.slice(1).toLowerCase();
}

export function capitalizeWords(value: string): string {
  return value
    .split(/\s+/)
    .map(capitalize)
    .filter(Boolean)
    .join(" ");
}

export function formatPatientName(
  lastname: string | null | undefined,
  name: string | null | undefined,
): string {
  const last = (lastname ?? "").trim().toUpperCase();
  const first = capitalizeWords(name ?? "");
  return [last, first].filter(Boolean).join(", ");
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("es-AR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("es-AR");
}

export function formatDni(value: string | null | undefined): string {
  return value || "—";
}

export function formatElapsed(
  createdAt: string | null | undefined,
  now: number = Date.now(),
): string {
  if (!createdAt) return "—";
  const minutes = Math.max(
    0,
    Math.floor((now - new Date(createdAt).getTime()) / 60_000),
  );
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    const restMinutes = minutes % 60;
    return restMinutes > 0 ? `${hours} h ${restMinutes} min` : `${hours} h`;
  }
  const days = Math.floor(hours / 24);
  const restHours = hours % 24;
  return restHours > 0 ? `${days} d ${restHours} h` : `${days} d`;
}
