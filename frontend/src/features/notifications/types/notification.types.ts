export type NotificationStatus = "SUCCESS" | "FAILED" | "PENDING";

export interface Notification {
  id: number;
  medical_order_id: number;
  pseudonym_hash: string;
  status: string;
  payload_sent: string;
  sent_at: string;
  error_message: string | null;
  patient_name: string | null;
  patient_lastname: string | null;
}
