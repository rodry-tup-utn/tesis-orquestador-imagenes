const COLUMNS = 6;

export default function OrdersTableSkeleton() {
  return (
    <tbody className="divide-y divide-gray-100">
      {Array.from({ length: 8 }).map((_, i) => (
        <tr key={i} className="animate-pulse">
          {Array.from({ length: COLUMNS }).map((_, j) => (
            <td key={j} className="px-4 py-4">
              <div className="h-4 rounded bg-gray-200" />
            </td>
          ))}
        </tr>
      ))}
    </tbody>
  );
}
