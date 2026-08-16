interface EmptyStateProps {
  message: string;
}

export default function EmptyState({ message }: EmptyStateProps) {
  return (
    <div className="px-4 py-12 text-center text-sm text-gray-500">{message}</div>
  );
}
