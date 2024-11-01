import { twMerge } from 'tailwind-merge';
import { ElectricityModeType } from 'types';

import ProductionSourceLegend from './ProductionSourceLegend';

export default function ProductionSourceLegendList({
  sources,
  className,
}: {
  sources: ElectricityModeType[];
  className?: string;
}) {
  return (
    <div className={twMerge('flex w-fit flex-row flex-wrap gap-2.5 py-1', className)}>
      {sources.map((source, index) => (
        <span key={source} className="flex items-center gap-1 text-sm">
          <ProductionSourceLegend key={index} electricityType={source} />
          <p>{source}</p>
        </span>
      ))}
    </div>
  );
}
