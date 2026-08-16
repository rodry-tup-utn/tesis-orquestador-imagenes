import type { OrderFilters } from "../features/orders/types/order.types";

export const queryKeys = {
  orders: ["orders"] as const,
  orderList: (filters: OrderFilters) => ["orders", "list", filters] as const,
  orderDetail: (id: number) => ["orders", "detail", id] as const,
  stats: ["stats"] as const,
  notifications: ["notifications"] as const,
  notificationsList: (offset: number, limit: number) =>
    ["notifications", "list", offset, limit] as const,
  triageRules: ["triage-rules"] as const,
  settings: ["settings"] as const,
};
