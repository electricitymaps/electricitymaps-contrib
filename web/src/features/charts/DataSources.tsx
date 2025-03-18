import * as Portal from '@radix-ui/react-portal';
import { Button } from 'components/Button';
import Link from 'components/Link';
import LabelTooltip from 'components/tooltips/LabelTooltip';
import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { TFunction } from 'i18next';
import { Info, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType } from 'types';
import { sourceLinkMapping } from 'utils/constants';
import { useBreakpoint } from 'utils/styling';

import { extractLinkFromSource } from './graphUtils';
import ProductionSourceLegend from './ProductionSourceLegend';

export function DataSources({
  title,
  icon,
  sources,
  emissionFactorSourcesToProductionSources,
}: {
  title: string;
  icon: React.ReactNode;
  sources: string[];
  emissionFactorSourcesToProductionSources?: { [key: string]: string[] };
}) {
  const { t } = useTranslation();
  const isMobile = !useBreakpoint('md');
  const showDataSources = Boolean(
    sources?.length > 0 ||
      Object.keys(emissionFactorSourcesToProductionSources || {}).length > 0
  );

  if (showDataSources == false) {
    return null;
  }

  return (
    <div className="flex flex-col py-2">
      <div className="flex items-center gap-1 pb-2">
        {icon}
        <p className="font-semibold">{title}</p>
        {emissionFactorSourcesToProductionSources && (
          <TooltipWrapper
            tooltipContent={
              isMobile ? (
                <EmissionFactorTooltip t={t} />
              ) : (
                <LabelTooltip className="max-w-[400px] text-start">
                  {t('country-panel.emissionFactorDataSourcesTooltip')}
                </LabelTooltip>
              )
            }
            side="bottom"
          >
            <Info className="text-emerald-800 dark:text-emerald-500" size={16} />
          </TooltipWrapper>
        )}
      </div>
      <div className="flex flex-col gap-2 pl-5">
        {sources.sort().map((source, index) => (
          <div key={index} className="text-sm">
            <Source source={source} />
            {emissionFactorSourcesToProductionSources && (
              <span className="inline-flex translate-y-1 gap-1 pl-1.5">
                {emissionFactorSourcesToProductionSources[source]?.map(
                  (productionSource, index) => (
                    <span key={index} className="self-center object-center text-xs">
                      <ProductionSourceLegend
                        electricityType={productionSource as ElectricityModeType}
                      />
                    </span>
                  )
                )}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function EmissionFactorTooltip({ t }: { t: TFunction<'translation', undefined> }) {
  return (
    <Portal.Root className="pointer-events-none absolute left-0 top-0 z-50 flex h-full w-full flex-col content-center items-center justify-center gap-2 bg-black/20 pb-40">
      <div className="dark:border-1 relative mx-6 h-auto min-w-64 rounded-xl border bg-zinc-50 p-4 text-left text-sm opacity-80 shadow-md dark:border-neutral-700 dark:bg-neutral-900">
        {t('country-panel.emissionFactorDataSourcesTooltip')}
      </div>
      <Button icon={<X />} type="secondary" backgroundClasses="pointer-events-auto" />
    </Portal.Root>
  );
}

function Source({ source }: { source: string }) {
  const link = extractLinkFromSource(source, sourceLinkMapping);
  if (link) {
    return <Link href={link}> {source} </Link>;
  }

  return <span>{source}</span>;
}
