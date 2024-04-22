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
    <div className={twMerge('flex flex-row gap-1.5 py-1', className)}>
      {sources.map((source, index) => (
        <ProductionSourceLegend key={index} electricityType={source} />
      ))}
    </div>
  );
}
