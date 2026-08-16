import { http } from "../../../services/http";
import type { Notification } from "../types/notification.types";

export async function listNotifications(
  offset = 0,
  limit = 20
): Promise<Notification[]> {
  const { data } = await http.get<Notification[]>("/orders/notifications", {
    params: { offset, limit },
  });
  return data;
}
