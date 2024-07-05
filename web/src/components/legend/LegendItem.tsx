import { ReactElement } from 'react';

function LegendItem({
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
      <p className="mr-2 pb-1 font-poppins text-sm">
        {label} <small>({unit})</small>
      </p>
      {children}
    </div>
  );
}

export default LegendItem;
