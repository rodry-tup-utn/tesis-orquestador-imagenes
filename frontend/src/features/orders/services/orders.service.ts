import { http } from "../../../services/http";
import type {
  MedicalOrderPagination,
  MedicalOrderRead,
  OrderFilters,
  UpdateObservationsPayload,
  UpdateStatePayload,
} from "../types/order.types";

export async function listOrders(
  params: OrderFilters,
): Promise<MedicalOrderPagination> {
  const { data } = await http.get<MedicalOrderPagination>("/orders", {
    params,
  });
  return data;
}

export async function getOrder(orderId: number): Promise<MedicalOrderRead> {
  const { data } = await http.get<MedicalOrderRead>(`/orders/${orderId}`);
  return data;
}

export async function updateOrderState(
  orderId: number,
  payload: UpdateStatePayload,
): Promise<MedicalOrderRead> {
  const { data } = await http.patch<MedicalOrderRead>(
    `/orders/${orderId}/state`,
    payload,
  );
  return data;
}

export async function updateOrderObservations(
  orderId: number,
  payload: UpdateObservationsPayload,
): Promise<MedicalOrderRead> {
  const { data } = await http.patch<MedicalOrderRead>(
    `/orders/${orderId}/observations`,
    payload,
  );
  return data;
}

export async function retriageOrder(
  orderId: number,
): Promise<MedicalOrderRead> {
  const { data } = await http.post<MedicalOrderRead>(
    `/orders/${orderId}/retriage`,
  );
  return data;
}

export async function sendOrderToOrthanc(
  orderId: number,
): Promise<MedicalOrderRead> {
  const { data } = await http.post<MedicalOrderRead>(
    `/orders/${orderId}/send-to-orthanc`,
  );
  return data;
}
