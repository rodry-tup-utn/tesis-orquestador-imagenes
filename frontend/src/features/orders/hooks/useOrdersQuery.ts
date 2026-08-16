import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { queryKeys } from "../../../lib/queryKeys";
import { getOrder, listOrders } from "../services/orders.service";
import type { OrderFilters } from "../types/order.types";

export function useOrdersQuery(filters: OrderFilters) {
  return useQuery({
    queryKey: queryKeys.orderList(filters),
    queryFn: () => listOrders(filters),
    placeholderData: keepPreviousData,
  });
}

export function useOrderQuery(orderId: number | null) {
  return useQuery({
    queryKey: queryKeys.orderDetail(orderId ?? -1),
    queryFn: () => getOrder(orderId as number),
    enabled: orderId != null,
  });
}
