export default function Spinner({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <div className="flex items-center justify-center py-10">
      <div
        className={`${className} animate-spin rounded-full border-2 border-sky-600 border-t-transparent`}
      />
    </div>
  );
}
