import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import Button from "../../../components/ui/Button";
import Card from "../../../components/ui/Card";
import ErrorState from "../../../components/ui/ErrorState";
import Input from "../../../components/ui/Input";
import Spinner from "../../../components/ui/Spinner";
import Toggle from "../../../components/ui/Toggle";
import { useSettings, useUpdateSettings } from "../hooks/useSettings";
import { formatDateTime } from "../../../lib/formatters";

export default function SettingsPage() {
  const { data, isPending, isError, error, refetch } = useSettings();
  const update = useUpdateSettings();

  const [form, setForm] = useState({
    notifications_enabled: true,
    notify_priority: false,
    triage_critical_threshold: 25,
    triage_urgent_threshold: 15,
    triage_priority_threshold: 10,
  });

  useEffect(() => {
    if (data) {
      setForm({
        notifications_enabled: data.notifications_enabled,
        notify_priority: data.notify_priority,
        triage_critical_threshold: data.triage_critical_threshold,
        triage_urgent_threshold: data.triage_urgent_threshold,
        triage_priority_threshold: data.triage_priority_threshold,
      });
    }
  }, [data]);

  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(false);
    update.mutate(
      {
        ...form,
        triage_critical_threshold: Number(form.triage_critical_threshold) || 0,
        triage_urgent_threshold: Number(form.triage_urgent_threshold) || 0,
        triage_priority_threshold: Number(form.triage_priority_threshold) || 0,
      },
      { onSuccess: () => setSaved(true) }
    );
  };

  if (isPending) return <Spinner />;

  if (isError || !data) {
    return (
      <ErrorState
        message={error?.message ?? "No se pudo cargar la configuración"}
        onRetry={() => void refetch()}
      />
    );
  }

  return (
    <div className="max-w-2xl space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Configuración</h1>
        <p className="text-sm text-gray-500">
          Parámetros globales del motor de triaje y notificaciones
        </p>
      </div>

      <Card title="Notificaciones">
        <div className="space-y-4 p-4">
          <Toggle
            checked={form.notifications_enabled}
            onChange={(v) => setForm((f) => ({ ...f, notifications_enabled: v }))}
            label="Notificaciones habilitadas"
            description="Enviar alertas a n8n / Telegram"
          />
          <Toggle
            checked={form.notify_priority}
            onChange={(v) => setForm((f) => ({ ...f, notify_priority: v }))}
            label="Notificar prioritarias"
            description="Además de las críticas, notificar órdenes prioritarias"
          />
        </div>
      </Card>

      <Card
        title="Umbrales de triaje"
        subtitle="La suma de pesos de las reglas que matchean determina la prioridad"
      >
        <div className="grid grid-cols-3 gap-3 p-4">
          <Input
            label="Crítico (≥)"
            type="number"
            value={form.triage_critical_threshold}
            onChange={(e) =>
              setForm((f) => ({ ...f, triage_critical_threshold: Number(e.target.value) }))
            }
          />
          <Input
            label="Urgente (≥)"
            type="number"
            value={form.triage_urgent_threshold}
            onChange={(e) =>
              setForm((f) => ({ ...f, triage_urgent_threshold: Number(e.target.value) }))
            }
          />
          <Input
            label="Prioritario (≥)"
            type="number"
            value={form.triage_priority_threshold}
            onChange={(e) =>
              setForm((f) => ({ ...f, triage_priority_threshold: Number(e.target.value) }))
            }
          />
        </div>
        <p className="px-4 pb-4 text-xs text-gray-500">
          Por debajo del umbral prioritario la orden queda como Rutina.
        </p>
      </Card>

      {update.error && (
        <ErrorState message={update.error.message} />
      )}

      <div className="flex items-center gap-3">
        <Button onClick={handleSave} loading={update.isPending} icon={<Save size={16} />}>
          Guardar cambios
        </Button>
        {saved && (
          <span className="text-sm font-medium text-green-600">
            Configuración guardada
          </span>
        )}
        <span className="ml-auto text-xs text-gray-400">
          Última actualización: {formatDateTime(data.updated_at)}
        </span>
      </div>
    </div>
  );
}
