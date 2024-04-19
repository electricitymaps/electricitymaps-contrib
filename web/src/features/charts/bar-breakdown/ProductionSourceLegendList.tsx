import { ElectricityModeType } from 'types';

import ProductionSourceLegend from './ProductionSourceLegend';

export default function ProductionSourceLegendList({
  sources,
}: {
  sources: ElectricityModeType[];
}) {
  return (
    <div className="flex flex-row gap-1.5 py-1">
      {sources.map((source, index) => (
        <ProductionSourceLegend key={index} electricityType={source} />
      ))}
    </div>
  );
}
