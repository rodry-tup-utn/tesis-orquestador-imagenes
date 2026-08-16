import type { TriageField, TriageOperator } from "../types/triageRule.types";

export const FIELD_LABELS: Record<TriageField, string> = {
  modality: "Modalidad",
  diagnosis: "Diagnóstico",
  origin_service: "Servicio de origen",
  patient_location: "Ubicación del paciente",
  is_urgent: "Urgente",
};

export const OPERATOR_LABELS: Record<TriageOperator, string> = {
  equals: "Igual a",
  contains: "Contiene",
  startswith: "Empieza con",
};

export const FIELDS: TriageField[] = [
  "modality",
  "diagnosis",
  "origin_service",
  "patient_location",
  "is_urgent",
];

export const OPERATORS: TriageOperator[] = ["equals", "contains", "startswith"];
