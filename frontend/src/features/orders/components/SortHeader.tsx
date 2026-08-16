import type { SortBy, SortDir } from "../types/order.types";

interface SortHeaderProps {
  label: string;
  sortBy: SortBy;
  active: SortBy;
  sortDir: SortDir;
  onSort: (field: SortBy) => void;
  dark?: boolean;
}

export default function SortHeader({
  label,
  sortBy,
  active,
  sortDir,
  onSort,
  dark = false,
}: SortHeaderProps) {
  const isActive = active === sortBy;
  return (
    <th className="px-4 py-3 text-center">
      <button
        type="button"
        onClick={() => onSort(sortBy)}
        className={`inline-flex items-center gap-1 text-center uppercase tracking-wide ${
          dark
            ? isActive
              ? "text-white"
              : "text-white/70 hover:text-white"
            : isActive
              ? "text-gray-900"
              : "text-gray-500 hover:text-gray-700"
        }`}
      >
        {label}
        <span className="text-xs">
          {isActive ? (sortDir === "asc" ? "▲" : "▼") : "↕"}
        </span>
      </button>
    </th>
  );
}
