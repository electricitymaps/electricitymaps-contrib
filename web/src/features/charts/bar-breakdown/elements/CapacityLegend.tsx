import { memo } from 'react';

function CapacityLegend({ text, unit }: { text: string; unit?: string }) {
  return (
    <div className="flex flex-row pt-2">
      <span className="mt-0.5 h-3 w-3 rounded-full bg-black/10 text-xs dark:bg-white/10" />
      <span className="pl-2 text-xs font-medium text-neutral-600 dark:text-neutral-300">
        {text} {unit && `(${unit})`}
      </span>
    </div>
  );
}

export default memo(CapacityLegend);
