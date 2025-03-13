export function DisabledMessage({ message }: { message: string }) {
  return (
    <div className="absolute left-1/2 top-1/2 z-10 min-w-56 -translate-x-1/2 -translate-y-1/2 rounded-lg border-neutral-200 bg-neutral-100 p-2 text-center text-sm shadow-lg dark:bg-neutral-800">
      {message}
    </div>
  );
}
