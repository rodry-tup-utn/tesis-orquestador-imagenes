import { useEffect, useState } from "react";
import { Plus, Save } from "lucide-react";
import Button from "../../../components/ui/Button";
import Input from "../../../components/ui/Input";
import Modal from "../../../components/ui/Modal";
import Select from "../../../components/ui/Select";
import Toggle from "../../../components/ui/Toggle";
import { FIELDS, FIELD_LABELS, OPERATOR_LABELS, OPERATORS } from "../constants/triageRule.constants";
import type {
  TriageField,
  TriageOperator,
  TriageRule,
  TriageRulePayload,
} from "../types/triageRule.types";

interface RuleFormModalProps {
  open: boolean;
  initial: TriageRule | null;
  loading?: boolean;
  error?: string;
  onClose: () => void;
  onSubmit: (payload: TriageRulePayload) => void;
}

const EMPTY: TriageRulePayload = {
  name: "",
  field: "modality",
  operator: "equals",
  value: "",
  weight: 0,
  enabled: true,
};

export default function RuleFormModal({
  open,
  initial,
  loading = false,
  error,
  onClose,
  onSubmit,
}: RuleFormModalProps) {
  const [form, setForm] = useState<TriageRulePayload>(EMPTY);

  useEffect(() => {
    if (open) {
      setForm(
        initial
          ? {
              name: initial.name,
              field: initial.field,
              operator: initial.operator,
              value: initial.value,
              weight: initial.weight,
              enabled: initial.enabled,
            }
          : EMPTY
      );
    }
  }, [open, initial]);

  const set = (patch: Partial<TriageRulePayload>) =>
    setForm((prev) => ({ ...prev, ...patch }));

  const canSubmit =
    form.name.trim().length > 0 && form.value.trim().length > 0;

  return (
    <Modal
      open={open}
      title={initial ? "Editar regla de triaje" : "Nueva regla de triaje"}
      onClose={onClose}
    >
      <div className="space-y-4">
        <Input
          label="Nombre"
          value={form.name}
          onChange={(e) => set({ name: e.target.value })}
          placeholder="Ej: ACV en guardia"
          maxLength={100}
        />
        <div className="grid grid-cols-2 gap-3">
          <Select
            label="Campo"
            value={form.field}
            onChange={(e) => set({ field: e.target.value as TriageField })}
          >
            {FIELDS.map((field) => (
              <option key={field} value={field}>
                {FIELD_LABELS[field]}
              </option>
            ))}
          </Select>
          <Select
            label="Operador"
            value={form.operator}
            onChange={(e) => set({ operator: e.target.value as TriageOperator })}
          >
            {OPERATORS.map((operator) => (
              <option key={operator} value={operator}>
                {OPERATOR_LABELS[operator]}
              </option>
            ))}
          </Select>
        </div>
        <Input
          label="Valor"
          value={form.value}
          onChange={(e) => set({ value: e.target.value })}
          placeholder="Ej: ACV, CT, UTI…"
          maxLength={255}
        />
        <Input
          label="Peso (puede ser negativo)"
          type="number"
          value={form.weight}
          onChange={(e) => set({ weight: Number(e.target.value) || 0 })}
        />
        <Toggle
          checked={form.enabled}
          onChange={(enabled) => set({ enabled })}
          label="Regla habilitada"
        />
        {error && (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
            {error}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            Cancelar
          </Button>
          <Button
            onClick={() => onSubmit(form)}
            loading={loading}
            disabled={!canSubmit}
            icon={initial ? <Save size={16} /> : <Plus size={16} />}
          >
            {initial ? "Guardar cambios" : "Crear regla"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
