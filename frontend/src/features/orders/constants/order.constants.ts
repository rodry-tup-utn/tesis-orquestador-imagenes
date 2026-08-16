import type { Modality, OrderSetting, OrderState } from "../types/order.types";

export const PAGE_SIZE = 10;

export const ORDER_STATES: OrderState[] = [
  "Pendiente",
  "En Proceso",
  "Finalizada",
  "Cancelada",
];

export const MODALITIES: Modality[] = [
  "CT",
  "MR",
  "US",
  "DX",
  "MG",
  "XA",
  "NM",
  "PT",
];

export const SOURCE_SYSTEMS: string[] = ["AMBULATORIO", "GUARDIA", "INTERNACION"];

export const STUDY_SETTINGS: OrderSetting[] = ["En Cama", "En Efector"];
