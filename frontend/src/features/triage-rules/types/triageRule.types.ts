export type TriageField =
  | "modality"
  | "diagnosis"
  | "origin_service"
  | "patient_location"
  | "is_urgent";

export type TriageOperator = "equals" | "contains" | "startswith";

export interface TriageRule {
  id: number;
  name: string;
  field: TriageField;
  operator: TriageOperator;
  value: string;
  weight: number;
  enabled: boolean;
  created_at: string;
}

export interface TriageRulePayload {
  name: string;
  field: TriageField;
  operator: TriageOperator;
  value: string;
  weight: number;
  enabled: boolean;
}
