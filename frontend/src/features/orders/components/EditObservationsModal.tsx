import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import Modal from "../../../components/ui/Modal";
import Button from "../../../components/ui/Button";
import Textarea from "../../../components/ui/Textarea";

interface EditObservationsModalProps {
  open: boolean;
  initial: string;
  loading?: boolean;
  error?: string;
  onClose: () => void;
  onSubmit: (observations: string) => void;
}

const MIN_LENGTH = 4;
const MAX_LENGTH = 255;

export default function EditObservationsModal({
  open,
  initial,
  loading = false,
  error,
  onClose,
  onSubmit,
}: EditObservationsModalProps) {
  const [value, setValue] = useState(initial);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setValue(initial);
      setLocalError(null);
    }
  }, [open, initial]);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (trimmed.length < MIN_LENGTH || trimmed.length > MAX_LENGTH) {
      setLocalError(
        `Debe tener entre ${MIN_LENGTH} y ${MAX_LENGTH} caracteres.`
      );
      return;
    }
    setLocalError(null);
    onSubmit(trimmed);
  };

  return (
    <Modal open={open} title="Editar observaciones" onClose={onClose}>
      <Textarea
        label="Observaciones"
        rows={5}
        value={value}
        maxLength={MAX_LENGTH}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Detalle clínico de la orden"
        disabled={loading}
      />
      <div className="mt-1 text-right text-xs text-gray-400">
        {value.length}/{MAX_LENGTH}
      </div>
      {(localError || error) && (
        <p className="mt-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          {localError ?? error}
        </p>
      )}
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose} disabled={loading}>
          Cancelar
        </Button>
        <Button onClick={handleSubmit} loading={loading} icon={<Save size={16} />}>
          Guardar
        </Button>
      </div>
    </Modal>
  );
}
