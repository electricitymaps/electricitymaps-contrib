import { Button } from 'components/Button';
import { twMerge } from 'tailwind-merge';
import { ElectricityModeType } from 'types';

import ProductionSourceLegend from './ProductionSourceLegend';

export default function ProductionSourceLegendList({
  sources,
  className,
  onToggleSelectedData,
  selectedData,
  isDataInteractive = false,
}: {
  sources: ElectricityModeType[];
  className?: string;
  onToggleSelectedData?: (source: ElectricityModeType) => void;
  selectedData?: Record<string, boolean>;
  isDataInteractive?: boolean;
}) {
  return (
    <div className={twMerge('flex w-fit flex-row flex-wrap gap-1 py-1', className)}>
      {sources.map((source, index) => {
        const onClick = () => onToggleSelectedData?.(source);
        const capitalizedLabel = `${source.charAt(0).toUpperCase()}${source.slice(1)}`;
        const isSourceSelected = selectedData && selectedData[source];

        return (
          <Button
            isDisabled={!isDataInteractive}
            key={index}
            type="tertiary"
            size="sm"
            foregroundClasses={'text-xs font-normal text-neutral-600 dark:text-gray-300'}
            backgroundClasses={isSourceSelected ? 'bg-neutral-400/10' : ''}
            onClick={onClick}
            icon={<ProductionSourceLegend key={index} electricityType={source} />}
          >
            {capitalizedLabel}
          </Button>
        );
      })}
    </div>
  );
}
