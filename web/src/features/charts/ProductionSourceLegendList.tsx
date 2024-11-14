import { Button } from 'components/Button';
import { twMerge } from 'tailwind-merge';
import { ElectricityModeType } from 'types';

import { SelectedData } from './OriginChart';
import ProductionSourceLegend from './ProductionSourceLegend';

export default function ProductionSourceLegendList({
  sources,
  className,
  selectedData,
  isDataInteractive = false,
}: {
  sources: ElectricityModeType[];
  className?: string;
  selectedData?: SelectedData;
  isDataInteractive?: boolean;
}) {
  // TODO(cady): memoize
  return (
    <div className={twMerge('flex w-fit flex-row flex-wrap gap-1 py-1', className)}>
      {sources.map((source, index) => {
        const onClick = () => selectedData?.toggle(source);
        const capitalizedLabel = `${source.charAt(0).toUpperCase()}${source.slice(1)}`;
        const isSourceSelected = selectedData?.isSelected(source);

        return (
          <Button
            isDisabled={!isDataInteractive}
            key={index}
            type="tertiary"
            size="sm"
            foregroundClasses={'text-xs font-normal text-neutral-600 dark:text-gray-300'}
            backgroundClasses={
              isSourceSelected
                ? 'outline outline-1 outline-neutral-200 bg-neutral-400/10 dark:bg-gray-600/80 dark:outline-gray-400/80'
                : ''
            }
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
