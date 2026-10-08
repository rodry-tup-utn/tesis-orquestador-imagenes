import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../lib/queryKeys";
import { clearAccessToken, getAccessToken } from "../services/auth";

export type WebSocketStatus = "connecting" | "connected" | "disconnected";

function resolveWsUrl(): string {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws`;
}

export function useWebSocket(): WebSocketStatus {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<WebSocketStatus>("connecting");

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    let closed = false;

    const handleMessage = (event: MessageEvent<string>) => {
      if (event.data === "authenticated") {
        setStatus("connected");
        attempt = 0;
        return;
      }
      if (event.data === "orders_updated") {
        void queryClient.invalidateQueries({ queryKey: queryKeys.orders });
        void queryClient.invalidateQueries({ queryKey: queryKeys.stats });
        void queryClient.invalidateQueries({ queryKey: queryKeys.notifications });
      }
    };

    const connect = () => {
      setStatus("connecting");
      ws = new WebSocket(resolveWsUrl());

      ws.onopen = () => {
        const token = getAccessToken();
        if (!token) {
          ws?.close(1008, "No autenticado");
          return;
        }
        if (ws) ws.send(JSON.stringify({ type: "auth", token }));
      };

      ws.onclose = (event) => {
        setStatus("disconnected");
        if (event.code === 1008) {
          // El backend rechazo el token (vencido o invalido): no tiene sentido reintentar.
          closed = true;
          clearAccessToken();
          if (window.location.pathname !== "/login") window.location.assign("/login");
          return;
        }
        if (!closed) {
          const delay = Math.min(1000 * 2 ** attempt, 15_000);
          attempt += 1;
          retryTimer = setTimeout(connect, delay);
        }
      };

      ws.onerror = () => { try { ws?.close(); } catch (_) {} };
      ws.onmessage = handleMessage;
    };

    connect();

    return () => {
      closed = true;
      if (retryTimer) clearTimeout(retryTimer);
      ws?.close();
    };
  }, [queryClient]);

  return status;
}
