import { ReactElement } from 'react';

export function LegendItem({
  label,
  unit,
  children,
}: {
  label: string;
  unit: string;
  children: ReactElement;
}) {
  return (
    <div className="text-center">
      <p className="whitespace-nowrap py-1 font-poppins">
        {label} <small>({unit})</small>
      </p>
      <div className="px-2">{children}</div>
    </div>
  );
}
