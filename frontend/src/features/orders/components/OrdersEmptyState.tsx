import { SearchX } from "lucide-react";

export default function OrdersEmptyState() {
  return (
    <tbody>
      <tr>
        <td colSpan={6} className="px-4 py-16 text-center">
          <SearchX className="mx-auto h-10 w-10 text-gray-300" />
          <p className="mt-3 text-sm font-medium text-gray-600">
            No se encontraron órdenes
          </p>
          <p className="mt-1 text-xs text-gray-400">
            Probá ajustar los filtros o la búsqueda.
          </p>
        </td>
      </tr>
    </tbody>
  );
}
