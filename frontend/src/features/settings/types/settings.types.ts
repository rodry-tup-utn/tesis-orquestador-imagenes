export interface SystemSettings {
  id: number;
  notifications_enabled: boolean;
  notify_priority: boolean;
  triage_critical_threshold: number;
  triage_urgent_threshold: number;
  triage_priority_threshold: number;
  updated_at: string;
}

export interface SystemSettingsUpdate {
  notifications_enabled?: boolean;
  notify_priority?: boolean;
  triage_critical_threshold?: number;
  triage_urgent_threshold?: number;
  triage_priority_threshold?: number;
}
