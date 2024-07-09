import * as Portal from '@radix-ui/react-portal';
import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { HiXMark } from 'react-icons/hi2';
import { twMerge } from 'tailwind-merge';
import { ElectricityModeType } from 'types';
import { useIsMobile } from 'utils/styling';

import ProductionSourceLegend from './ProductionSourceLegend';

export default function ProductionSourceLegendList({
  sources,
  className,
}: {
  sources: ElectricityModeType[];
  className?: string;
}) {
  const isMobile = useIsMobile();

  return (
    <TooltipWrapper
      tooltipContent={<ProductionSourceTooltip sources={sources} isMobile={isMobile} />}
      tooltipClassName={
        isMobile
          ? 'absolute h-full min-w-44 rounded-none border-0 p-0 text-left text-lg shadow-none dark:border-white dark:bg-gray-900'
          : 'rounded-xl min-w-44 dark:bg-gray-900 dark:border-1 dark:border-gray-700'
      }
      side="bottom"
      isMobile={isMobile}
    >
      <div className={twMerge('flex w-fit flex-row gap-1.5 py-1', className)}>
        {sources.map((source, index) => (
          <ProductionSourceLegend key={index} electricityType={source} />
        ))}
      </div>
    </TooltipWrapper>
  );
}

function ProductionSourceTooltip({
  sources,
  isMobile,
}: {
  sources: ElectricityModeType[];
  isMobile: boolean;
}) {
  if (isMobile) {
    return (
      <Portal.Root className="pointer-events-none absolute left-0 top-0 z-50 flex h-full w-full flex-col content-center items-center justify-center bg-black/20 pb-40">
        <div className="dark:border-1 relative mx-6 h-auto min-w-64 rounded-xl border bg-zinc-50 p-4 text-left text-sm opacity-80 shadow-md dark:border-gray-700 dark:bg-gray-900">
          <div className="flex flex-col gap-1.5">
            {sources.map((source, index) => (
              <div key={source} className="flex flex-row gap-2">
                <ProductionSourceLegend key={index} electricityType={source} />
                <div className="text-xs font-medium">{source}</div>
              </div>
            ))}
          </div>
        </div>
        <button className="p-auto pointer-events-auto mt-2 flex h-10 w-10 items-center justify-center self-center rounded-full border bg-zinc-50 text-black shadow-md">
          <HiXMark size="24" />
        </button>
      </Portal.Root>
    );
  }

  return (
    <div className="flex flex-col gap-1.5">
      {sources.map((source, index) => (
        <div key={source} className="flex flex-row gap-2">
          <ProductionSourceLegend key={index} electricityType={source} />
          <div className="text-xs font-medium">{source}</div>
        </div>
      ))}
    </div>
  );
}
