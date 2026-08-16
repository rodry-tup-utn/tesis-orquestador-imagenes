import { http } from "../../../services/http";
import type { Notification } from "../../notifications/types/notification.types";
import type { OrderStats } from "../../orders/types/order.types";

export async function getOrderStats(): Promise<OrderStats> {
  const { data } = await http.get<OrderStats>("/orders/stats");
  return data;
}

export async function getLatestNotifications(
  limit = 5
): Promise<Notification[]> {
  const { data } = await http.get<Notification[]>("/orders/notifications", {
    params: { limit },
  });
  return data;
}
