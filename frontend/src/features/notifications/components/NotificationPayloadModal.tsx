import { useState } from "react";
import Modal from "../../../components/ui/Modal";

interface NotificationPayloadModalProps {
  open: boolean;
  payload: string;
  onClose: () => void;
}

function prettyPayload(payload: string): string {
  try {
    return JSON.stringify(JSON.parse(payload), null, 2);
  } catch {
    return payload;
  }
}

export default function NotificationPayloadModal({
  open,
  payload,
  onClose,
}: NotificationPayloadModalProps) {
  return (
    <Modal open={open} title="Payload enviado a n8n" onClose={onClose} wide>
      <pre className="max-h-[60vh] overflow-auto rounded-md bg-gray-900 p-4 text-xs leading-relaxed text-gray-100">
        {prettyPayload(payload)}
      </pre>
    </Modal>
  );
}

export function usePayloadModal() {
  const [payload, setPayload] = useState<string | null>(null);
  return {
    payload,
    open: (p: string) => setPayload(p),
    close: () => setPayload(null),
  };
}
