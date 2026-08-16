import Modal from "../../../components/ui/Modal";
import Button from "../../../components/ui/Button";
import { ORDER_STATES } from "../constants/order.constants";
import type { OrderState } from "../types/order.types";

interface ChangeStateModalProps {
  open: boolean;
  current: OrderState;
  loading?: boolean;
  error?: string;
  onClose: () => void;
  onSubmit: (state: OrderState) => void;
}

export default function ChangeStateModal({
  open,
  current,
  loading = false,
  error,
  onClose,
  onSubmit,
}: ChangeStateModalProps) {
  return (
    <Modal open={open} title="Cambiar estado de la orden" onClose={onClose}>
      <div className="space-y-2">
        {ORDER_STATES.map((state) => (
          <button
            key={state}
            type="button"
            disabled={loading}
            onClick={() => onSubmit(state)}
            className={`flex w-full items-center justify-between rounded-md border px-3 py-2 text-sm transition-colors disabled:opacity-50 ${
              state === current
                ? "border-sky-500 bg-sky-50 text-sky-700"
                : "border-gray-200 text-gray-700 hover:bg-gray-50"
            }`}
          >
            <span>{state}</span>
            {state === current && <span className="text-xs">Actual</span>}
          </button>
        ))}
      </div>
      {error && (
        <p className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          {error}
        </p>
      )}
      <div className="mt-4 flex justify-end">
        <Button variant="secondary" onClick={onClose} disabled={loading}>
          Cerrar
        </Button>
      </div>
    </Modal>
  );
}
