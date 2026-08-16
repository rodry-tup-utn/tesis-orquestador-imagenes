import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../../lib/queryKeys";
import type { ApiError } from "../../../services/http";
import {
  retriageOrder,
  sendOrderToOrthanc,
  updateOrderObservations,
  updateOrderState,
} from "../services/orders.service";
import type { OrderState } from "../types/order.types";

function invalidateOrdersData(queryClient: QueryClient) {
  void queryClient.invalidateQueries({ queryKey: queryKeys.orders });
  void queryClient.invalidateQueries({ queryKey: queryKeys.stats });
}

export function useUpdateOrderState() {
  const queryClient = useQueryClient();
  return useMutation<
    unknown,
    ApiError,
    { id: number; state: OrderState }
  >({
    mutationFn: ({ id, state }) => updateOrderState(id, { order_state: state }),
    onSuccess: () => invalidateOrdersData(queryClient),
  });
}

export function useUpdateOrderObservations() {
  const queryClient = useQueryClient();
  return useMutation<unknown, ApiError, { id: number; observations: string }>({
    mutationFn: ({ id, observations }) =>
      updateOrderObservations(id, { observations }),
    onSuccess: () => invalidateOrdersData(queryClient),
  });
}

export function useRetriageOrder() {
  const queryClient = useQueryClient();
  return useMutation<unknown, ApiError, number>({
    mutationFn: (id) => retriageOrder(id),
    onSuccess: () => invalidateOrdersData(queryClient),
  });
}

export function useSendOrderToOrthanc() {
  const queryClient = useQueryClient();
  return useMutation<unknown, ApiError, number>({
    mutationFn: (id) => sendOrderToOrthanc(id),
    onSuccess: () => invalidateOrdersData(queryClient),
  });
}
