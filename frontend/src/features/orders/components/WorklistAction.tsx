import { useState } from "react";
import { RotateCw, Send } from "lucide-react";
import Button from "../../../components/ui/Button";
import ConfirmDialog from "../../../components/ui/ConfirmDialog";
import { useSendOrderToOrthanc } from "../hooks/useOrderMutations";
import type { MedicalOrderRead } from "../types/order.types";

interface WorklistActionProps {
  order: MedicalOrderRead;
  iconOnly?: boolean;
  compact?: boolean;
}

export default function WorklistAction({
  order,
  iconOnly = false,
  compact = false,
}: WorklistActionProps) {
  const [open, setOpen] = useState(false);
  const orthancMutation = useSendOrderToOrthanc();
  const orderId = order.id;
  const sent = order.sent_to_orthanc;

  return (
    <div className="flex flex-wrap items-center justify-center gap-1">
      <Button
        size={compact ? "xs" : "sm"}
        variant={sent ? "soft-success" : "primary"}
        icon={sent ? <RotateCw size={14} /> : <Send size={14} />}
        iconOnly={iconOnly}
        onClick={() => setOpen(true)}
        title="Generar worklist y enviar a Orthanc"
      >
        {sent ? "Reenviar a worklist" : "Enviar a  worklist"}
      </Button>

      <ConfirmDialog
        open={open}
        title="Enviar a Worklist"
        message={
          sent
            ? `La orden ${order.external_id} ya tiene la worklist enviada. ¿Desea generarla y enviarla nuevamente?`
            : `Se generará la worklist DICOM de la orden ${order.external_id} y se enviará al servidor Orthanc.`
        }
        confirmLabel="Enviar"
        loading={orthancMutation.isPending}
        error={orthancMutation.error?.message}
        onClose={() => setOpen(false)}
        onConfirm={() =>
          orderId != null &&
          orthancMutation.mutate(orderId, {
            onSuccess: () => setOpen(false),
          })
        }
      />
    </div>
  );
}
