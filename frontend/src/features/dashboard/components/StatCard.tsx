import Card from "../../../components/ui/Card";

interface StatCardProps {
  label: string;
  value: number | string;
  accent?: string;
}

export default function StatCard({ label, value, accent = "text-gray-900" }: StatCardProps) {
  return (
    <Card className="px-4 py-5">
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
        {label}
      </p>
      <p className={`mt-1 text-3xl font-semibold ${accent}`}>{value}</p>
    </Card>
  );
}
