import { Pencil, Trash2 } from "lucide-react";
import Button from "../../../components/ui/Button";
import { FIELD_LABELS, OPERATOR_LABELS } from "../constants/triageRule.constants";
import type { TriageRule } from "../types/triageRule.types";

interface TriageRulesTableProps {
  rules: TriageRule[];
  loading: boolean;
  onEdit: (rule: TriageRule) => void;
  onDelete: (rule: TriageRule) => void;
  onToggle: (rule: TriageRule) => void;
  togglePending?: boolean;
}

export default function TriageRulesTable({
  rules,
  loading,
  onEdit,
  onDelete,
  onToggle,
  togglePending = false,
}: TriageRulesTableProps) {
  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-5 animate-pulse rounded bg-gray-200" />
        ))}
      </div>
    );
  }

  if (rules.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white px-4 py-12 text-center text-sm text-gray-500 shadow-sm">
        No hay reglas de triaje configuradas.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Nombre</th>
              <th className="px-4 py-3">Campo</th>
              <th className="px-4 py-3">Operador</th>
              <th className="px-4 py-3">Valor</th>
              <th className="px-4 py-3">Peso</th>
              <th className="px-4 py-3">Habilitada</th>
              <th className="px-4 py-3">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rules.map((rule) => (
              <tr key={rule.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {rule.name}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {FIELD_LABELS[rule.field]}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {OPERATOR_LABELS[rule.operator]}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-gray-700">
                  {rule.value}
                </td>
                <td
                  className={`px-4 py-3 text-sm font-semibold ${
                    rule.weight > 0
                      ? "text-green-700"
                      : rule.weight < 0
                        ? "text-red-600"
                        : "text-gray-600"
                  }`}
                >
                  {rule.weight}
                </td>
                <td className="px-4 py-3">
                  <button
                    type="button"
                    disabled={togglePending}
                    onClick={() => onToggle(rule)}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                      rule.enabled ? "bg-sky-600" : "bg-gray-300"
                    }`}
                    title={rule.enabled ? "Deshabilitar" : "Habilitar"}
                  >
                    <span
                      className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
                        rule.enabled ? "translate-x-5" : "translate-x-1"
                      }`}
                    />
                  </button>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="soft-neutral"
                      icon={<Pencil size={14} />}
                      onClick={() => onEdit(rule)}
                    >
                      Editar
                    </Button>
                    <Button
                      size="sm"
                      variant="soft-danger"
                      icon={<Trash2 size={14} />}
                      onClick={() => onDelete(rule)}
                    >
                      Eliminar
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
