import { Button } from 'components/Button';
import { twMerge } from 'tailwind-merge';
import { ElectricityModeType } from 'types';
import { useIsMobile } from 'utils/styling';

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
  const isMobile = useIsMobile();

  return (
    <div className={twMerge('flex w-fit flex-row flex-wrap gap-1 py-1', className)}>
      {sources.map((source, index) => {
        const onClick = () => onToggleSelectedData?.(source);
        const isSourceFocused = selectedData && selectedData[source];
        return (
          <Button
            isDisabled={!isDataInteractive}
            key={index}
            type="tertiary"
            size="sm"
            foregroundClasses={'font-normal'}
            backgroundClasses={isSourceFocused ? 'bg-neutral-400/10' : ''}
            onClick={onClick}
            icon={<ProductionSourceLegend key={index} electricityType={source} />}
          >
            {source}
          </Button>
        );
      })}
    </div>
  );
}
