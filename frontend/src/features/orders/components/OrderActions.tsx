import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, MessageSquare, RotateCcw, ToggleRight } from "lucide-react";
import Button from "../../../components/ui/Button";
import ConfirmDialog from "../../../components/ui/ConfirmDialog";
import {
  useRetriageOrder,
  useUpdateOrderObservations,
  useUpdateOrderState,
} from "../hooks/useOrderMutations";
import type { MedicalOrderRead } from "../types/order.types";
import ChangeStateModal from "./ChangeStateModal";
import EditObservationsModal from "./EditObservationsModal";
import WorklistAction from "./WorklistAction";

interface OrderActionsProps {
  order: MedicalOrderRead;
  showDetailButton?: boolean;
  showRetriage?: boolean;
  iconOnly?: boolean;
  compact?: boolean;
  vertical?: boolean;
  size?: "xs" | "sm" | "md";
}

export default function OrderActions({
  order,
  showDetailButton: detailButton = true,
  showRetriage = true,
  iconOnly = false,
  compact = false,
  vertical = false,
  size,
}: OrderActionsProps) {
  const [stateOpen, setStateOpen] = useState(false);
  const [obsOpen, setObsOpen] = useState(false);
  const [retriageOpen, setRetriageOpen] = useState(false);
  const navigate = useNavigate();

  const stateMutation = useUpdateOrderState();
  const obsMutation = useUpdateOrderObservations();
  const retriageMutation = useRetriageOrder();

  const orderId = order.id;
  const hasObservations =
    Boolean(order.order.observations?.trim()) &&
    !(order.order.observations?.toLowerCase() == "sin observaciones");
  const buttonSize = size ?? (compact ? "xs" : "sm");
  const iconSize = buttonSize === "md" ? 16 : 14;

  const goToDetail = () => {
    if (orderId != null) navigate(`/orders/${orderId}`);
  };

  return (
    <div
      className={
        vertical
          ? "flex flex-col gap-2"
          : "flex flex-wrap items-center justify-center gap-1"
      }
    >
      {detailButton && (
        <Button
          size={buttonSize}
          variant="primary"
          icon={<Eye size={iconSize} />}
          iconOnly={iconOnly}
          onClick={goToDetail}
          title="Ver detalle de la orden"
        >
          Ver detalle
        </Button>
      )}
      <Button
        size={buttonSize}
        variant="soft-primary"
        icon={<ToggleRight size={iconSize} />}
        iconOnly={iconOnly}
        onClick={() => setStateOpen(true)}
        title="Cambiar estado"
      >
        Cambiar estado
      </Button>
      {showRetriage && (
        <Button
          size={buttonSize}
          variant="soft-warning"
          icon={<RotateCcw size={iconSize} />}
          iconOnly={iconOnly}
          onClick={() => setRetriageOpen(true)}
          title="Re-evaluar triaje"
        >
          Re-triaje
        </Button>
      )}
      <Button
        size={buttonSize}
        variant={hasObservations ? "warning" : "ghost-warning"}
        icon={<MessageSquare size={iconSize} fill="currentColor" />}
        iconOnly={iconOnly}
        onClick={() => setObsOpen(true)}
        title="Ver o editar observaciones"
      >
        Observaciones
      </Button>

      <WorklistAction order={order} size={buttonSize} block={vertical} />

      <ChangeStateModal
        open={stateOpen}
        current={order.order.state}
        loading={stateMutation.isPending}
        error={stateMutation.error?.message}
        onClose={() => setStateOpen(false)}
        onSubmit={(state) =>
          orderId != null &&
          stateMutation.mutate(
            { id: orderId, state },
            { onSuccess: () => setStateOpen(false) },
          )
        }
      />

      <EditObservationsModal
        open={obsOpen}
        initial={order.order.observations ?? ""}
        loading={obsMutation.isPending}
        error={obsMutation.error?.message}
        onClose={() => setObsOpen(false)}
        onSubmit={(observations) =>
          orderId != null &&
          obsMutation.mutate(
            { id: orderId, observations },
            { onSuccess: () => setObsOpen(false) },
          )
        }
      />

      <ConfirmDialog
        open={retriageOpen}
        title="Re-evaluar triaje"
        message={`Se volverán a aplicar las reglas de triaje vigentes a la orden ${order.external_id}. La prioridad puede cambiar.`}
        confirmLabel="Re-evaluar"
        loading={retriageMutation.isPending}
        error={retriageMutation.error?.message}
        onClose={() => setRetriageOpen(false)}
        onConfirm={() =>
          orderId != null &&
          retriageMutation.mutate(orderId, {
            onSuccess: () => setRetriageOpen(false),
          })
        }
      />
    </div>
  );
}
