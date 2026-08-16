import { NavLink, Outlet } from "react-router-dom";
import { useWebSocket } from "../../hooks/useWebSocket";
import type { WebSocketStatus } from "../../hooks/useWebSocket";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/orders", label: "Órdenes" },
  { to: "/notifications", label: "Notificaciones" },
  { to: "/triage-rules", label: "Reglas de triaje" },
  { to: "/settings", label: "Configuración" },
];

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-2 text-sm font-medium ${
    isActive
      ? "bg-sky-100 text-sky-700"
      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
  }`;

const WS_STATUS_LABELS: Record<WebSocketStatus, string> = {
  connecting: "Conectando…",
  connected: "Tiempo real conectado",
  disconnected: "Sin conexión en tiempo real",
};

const WS_STATUS_COLORS: Record<WebSocketStatus, string> = {
  connecting: "bg-yellow-400",
  connected: "bg-green-500",
  disconnected: "bg-red-500",
};

export default function AppLayout() {
  const wsStatus = useWebSocket();

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
          <span className="text-lg font-semibold text-gray-900">
            Servicio de Imágenes
          </span>
          <nav className="flex gap-2">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={navClass}
                end={item.to === "/dashboard"}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span
              title={WS_STATUS_LABELS[wsStatus]}
              className={`inline-block h-2.5 w-2.5 rounded-full ${WS_STATUS_COLORS[wsStatus]}`}
            />
            {WS_STATUS_LABELS[wsStatus]}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
