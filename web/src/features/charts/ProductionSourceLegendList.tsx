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
          ? 'bg-transparent shadow-none border-transparent dark:bg-transparent items-center flex flex-col p-0 mb-2'
          : 'rounded-2xl min-w-44 dark:bg-gray-900/80 dark:border-1 dark:border-gray-700 mx-5 backdrop-blur bg-white/80 mb-2'
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
      <>
        <div className="dark:border-1 relative h-auto min-w-44 rounded-2xl border bg-white/80 p-4 text-left text-sm shadow-md backdrop-blur dark:border-gray-700 dark:bg-gray-900/80">
          <ProductionSourceTooltipInner sources={sources} />
        </div>
        <button className="p-auto pointer-events-auto mt-2 flex h-10 w-10 items-center justify-center self-center rounded-full border bg-white text-black shadow-md">
          <HiXMark size="24" />
        </button>
      </>
    );
  }

  return <ProductionSourceTooltipInner sources={sources} />;
}

function ProductionSourceTooltipInner({ sources }: { sources: ElectricityModeType[] }) {
  return (
    <div className="flex flex-col gap-1.5">
      {sources.map((source) => (
        <div key={source} className="flex flex-row gap-2">
          <ProductionSourceLegend key={source} electricityType={source} />
          <div className="text-xs font-medium">{source}</div>
        </div>
      ))}
    </div>
  );
}
