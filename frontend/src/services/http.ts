import axios from "axios";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

export interface ApiError {
  status?: number;
  message: string;
}

function extractDetail(data: unknown): string | null {
  if (typeof data === "string") return data;
  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    if (typeof obj.detail === "string") return obj.detail;
    if (Array.isArray(obj.detail)) {
      return obj.detail
        .map((item) => {
          if (item && typeof item === "object") {
            const loc = (item as Record<string, unknown>).loc;
            const msg = (item as Record<string, unknown>).msg;
            const field = Array.isArray(loc) ? loc[loc.length - 1] : loc;
            return `${field}: ${msg}`;
          }
          return String(item);
        })
        .join("; ");
    }
  }
  return null;
}

http.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    const apiError: ApiError = { message: "Error de conexión con el servidor" };

    if (axios.isAxiosError(error)) {
      apiError.status = error.response?.status;
      const detail = extractDetail(error.response?.data);
      apiError.message =
        detail ?? (error.response ? `Error ${error.response.status}` : error.message);
    } else {
      apiError.message =
        error instanceof Error ? error.message : "Error desconocido";
    }

    return Promise.reject(apiError);
  }
);
