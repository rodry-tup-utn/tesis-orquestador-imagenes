import type { SelectHTMLAttributes } from "react";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
}

export default function Select({ label, className = "", children, ...props }: SelectProps) {
  return (
    <label className="block">
      {label && (
        <span className="mb-1 block text-xs font-medium text-gray-700">
          {label}
        </span>
      )}
      <select
        className={`w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 ${className}`}
        {...props}
      >
        {children}
      </select>
    </label>
  );
}
