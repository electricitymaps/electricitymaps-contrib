import { Button } from 'components/Button';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
  // TODO(cady): memoize
  return (
    <div className={twMerge('flex w-fit flex-row flex-wrap gap-1 py-1', className)}>
      {sources.map((source, index) => {
        const onClick = () => selectedData?.toggle(source);
        const translatedSource = t(source.toLowerCase());
        const capitalizedLabel = `${translatedSource
          .charAt(0)
          .toUpperCase()}${translatedSource.slice(1)}`;
        const isSourceSelected = selectedData?.isSelected(source);

        return (
          <Button
            isDisabled={!isDataInteractive}
            key={index}
            type="tertiary"
            size="sm"
            foregroundClasses={twMerge(
              'text-xs font-normal text-neutral-600 dark:text-gray-300',
              isSourceSelected && 'text-neutral-800 dark:text-white'
            )}
            backgroundClasses={twMerge(
              isSourceSelected &&
                'outline outline-1 outline-neutral-200 bg-neutral-400/10 dark:bg-gray-600/80 dark:outline-gray-400/50'
            )}
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
