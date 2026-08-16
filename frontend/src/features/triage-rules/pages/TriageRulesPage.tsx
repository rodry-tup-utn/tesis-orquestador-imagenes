import { useState } from "react";
import { Plus } from "lucide-react";
import Button from "../../../components/ui/Button";
import ConfirmDialog from "../../../components/ui/ConfirmDialog";
import ErrorState from "../../../components/ui/ErrorState";
import {
  useCreateTriageRule,
  useDeleteTriageRule,
  useTriageRules,
  useUpdateTriageRule,
} from "../hooks/useTriageRules";
import type { TriageRule } from "../types/triageRule.types";
import RuleFormModal from "../components/RuleFormModal";
import TriageRulesTable from "../components/TriageRulesTable";

export default function TriageRulesPage() {
  const { data, isPending, isError, error, refetch } = useTriageRules();

  const create = useCreateTriageRule();
  const update = useUpdateTriageRule();
  const remove = useDeleteTriageRule();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<TriageRule | null>(null);
  const [deleting, setDeleting] = useState<TriageRule | null>(null);
  const [togglePendingId, setTogglePendingId] = useState<number | null>(null);

  const rules = data ?? [];

  const openCreate = () => {
    setEditing(null);
    setFormOpen(true);
  };

  const openEdit = (rule: TriageRule) => {
    setEditing(rule);
    setFormOpen(true);
  };

  const closeForm = () => {
    if (create.isPending || update.isPending) return;
    setFormOpen(false);
    setEditing(null);
  };

  const handleToggle = (rule: TriageRule) => {
    setTogglePendingId(rule.id);
    update.mutate(
      {
        id: rule.id,
        payload: {
          name: rule.name,
          field: rule.field,
          operator: rule.operator,
          value: rule.value,
          weight: rule.weight,
          enabled: !rule.enabled,
        },
      },
      { onSettled: () => setTogglePendingId(null) }
    );
  };

  const mutationError = create.error?.message ?? update.error?.message ?? undefined;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">
            Reglas de triaje
          </h1>
          <p className="text-sm text-gray-500">
            {rules.length} regla(s) configuradas para el motor de priorización
          </p>
        </div>
        <Button onClick={openCreate} icon={<Plus size={16} />}>
          Nueva regla
        </Button>
      </div>

      {isError && (
        <ErrorState
          message={error?.message ?? "Error al cargar las reglas"}
          onRetry={() => void refetch()}
        />
      )}

      <TriageRulesTable
        rules={rules}
        loading={isPending}
        onEdit={openEdit}
        onDelete={setDeleting}
        onToggle={handleToggle}
        togglePending={togglePendingId != null}
      />

      <RuleFormModal
        open={formOpen}
        initial={editing}
        loading={create.isPending || update.isPending}
        error={mutationError}
        onClose={closeForm}
        onSubmit={(payload) => {
          const onSuccess = () => {
            setFormOpen(false);
            setEditing(null);
          };
          if (editing) {
            update.mutate({ id: editing.id, payload }, { onSuccess });
          } else {
            create.mutate(payload, { onSuccess });
          }
        }}
      />

      <ConfirmDialog
        open={deleting != null}
        title="Eliminar regla de triaje"
        message={`¿Eliminar la regla "${deleting?.name}"? Esta acción no se puede deshacer.`}
        confirmLabel="Eliminar"
        loading={remove.isPending}
        error={remove.error?.message}
        onClose={() => setDeleting(null)}
        onConfirm={() =>
          deleting &&
          remove.mutate(deleting.id, { onSuccess: () => setDeleting(null) })
        }
      />
    </div>
  );
}
