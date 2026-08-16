import { http } from "../../../services/http";
import type { SystemSettings, SystemSettingsUpdate } from "../types/settings.types";

export async function getSettings(): Promise<SystemSettings> {
  const { data } = await http.get<SystemSettings>("/settings");
  return data;
}

export async function updateSettings(
  payload: SystemSettingsUpdate
): Promise<SystemSettings> {
  const { data } = await http.patch<SystemSettings>("/settings", payload);
  return data;
}
