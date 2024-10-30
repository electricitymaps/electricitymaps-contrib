import { Button } from 'components/Button';
import { twMerge } from 'tailwind-merge';
import { ElectricityModeType } from 'types';

import ProductionSourceLegend from './ProductionSourceLegend';

export default function ProductionSourceLegendList({
  sources,
  className,
  onToggleFocus,
  focusedData,
}: {
  sources: ElectricityModeType[];
  className?: string;
  onToggleFocus?: (source: ElectricityModeType) => void;
  focusedData?: Set<string>;
}) {
  return (
    <div className={twMerge('flex w-fit flex-row flex-wrap gap-1 py-1', className)}>
      {sources.map((source, index) => {
        // TODO(cady): handle this?
        const onClick = () => onToggleFocus?.(source);
        return (
          <Button
            key={index}
            type="tertiary"
            size="sm"
            foregroundClasses={'font-normal'}
            backgroundClasses={focusedData?.has(source) ? 'bg-neutral-400/10' : ''}
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
