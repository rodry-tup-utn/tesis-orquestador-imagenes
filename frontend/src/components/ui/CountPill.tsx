interface CountPillProps {
  tipo: string;
  valor: number;
  accent?: "sky" | "red" | "orange" | "gray";
}

const ACCENT_CLASSES: Record<NonNullable<CountPillProps["accent"]>, string> = {
  sky: "bg-sky-50 text-sky-800 ring-sky-600/20",
  red: "bg-red-50 text-red-700 ring-red-600/20",
  orange: "bg-orange-50 text-orange-700 ring-orange-600/20",
  gray: "bg-gray-50 text-gray-700 ring-gray-600/20",
};

export default function CountPill({
  tipo,
  valor,
  accent = "sky",
}: CountPillProps) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium ring-1 ${ACCENT_CLASSES[accent]}`}
    >
      {tipo}
      <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold tabular-nums shadow-sm">
        {valor}
      </span>
    </span>
  );
}
