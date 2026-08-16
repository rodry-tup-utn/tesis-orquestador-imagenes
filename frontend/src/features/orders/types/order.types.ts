export type Modality = "CT" | "MR" | "US" | "DX" | "MG" | "XA" | "NM" | "PT";

export type OrderSetting = "En Cama" | "En Efector";

export type Sex = "MALE" | "FEMALE" | "OTHER";

export type OrderState = "Pendiente" | "En Proceso" | "Finalizada" | "Cancelada";

export type MedicalPriority = "Crítico" | "Urgente" | "Prioritario" | "Rutina";

export type SortBy = "created_at" | "priority" | "patient_name";

export type SortDir = "asc" | "desc";

export interface PatientInfo {
  name: string;
  lastname: string;
  pseudonym: string;
  dni: string;
  dob: string;
  sex: Sex;
}

export interface OrderDetails {
  modality: Modality;
  description: string;
  location: string;
  study_setting: OrderSetting;
  diagnosis: string;
  observations: string | null;
  date: string;
  requesting_physician: string;
  original_priority: string;
  triage_priority: MedicalPriority;
  state: OrderState;
}

export interface MedicalOrderRead {
  id: number | null;
  external_id: string;
  source_system: string;
  created_at: string;
  was_notified: boolean;
  sent_to_orthanc: boolean;
  study_instance_uid: string | null;
  patient: PatientInfo;
  order: OrderDetails;
}

export interface MedicalOrderPagination {
  items: MedicalOrderRead[];
  total: number;
}

export interface OrderFilters {
  offset?: number;
  limit?: number;
  q?: string;
  patient_dni?: string;
  start_date?: string;
  end_date?: string;
  order_state?: OrderState;
  was_notified?: boolean;
  modality?: Modality;
  source_system?: string;
  study_setting?: OrderSetting;
  sort_by?: SortBy;
  sort_dir?: SortDir;
}

export interface UpdateStatePayload {
  order_state: OrderState;
}

export interface UpdateObservationsPayload {
  observations: string;
}

export interface OrderStats {
  total: number;
  notified: number;
  critical_pending: number;
  by_state: Record<string, number>;
  by_priority: Record<string, number>;
  by_modality: Record<string, number>;
  latest_created_at: string | null;
}
