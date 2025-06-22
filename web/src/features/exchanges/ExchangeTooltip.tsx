import { CarbonIntensityDisplay } from 'components/CarbonIntensityDisplay';
import GlassContainer from 'components/GlassContainer';
import { ZoneName } from 'components/ZoneName';
import { useAtomValue } from 'jotai';
import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import { twMerge } from 'tailwind-merge';
import { ExchangeArrowData } from 'types';
import { formatEnergy, formatPower } from 'utils/formatting';
import { isHourlyAtom } from 'utils/state/atoms';

interface ExchangeTooltipProperties {
  exchangeData: ExchangeArrowData;
  isMobile: boolean;
  className?: string;
}

export default function ExchangeTooltip({
  exchangeData,
  isMobile,
  className,
}: ExchangeTooltipProperties): ReactElement {
  const { t } = useTranslation();
  const isHourly = useAtomValue(isHourlyAtom);
  const { key, netFlow, co2intensity } = exchangeData;

  const isExporting = netFlow > 0;
  const roundedNetFlow = Math.abs(Math.round(netFlow));
  const zoneFrom = key.split('->')[isExporting ? 0 : 1];
  const zoneTo = key.split('->')[isExporting ? 1 : 0];

  const divClass = `${isMobile ? 'flex-col' : 'flex'} items-center pb-2`;
  return (
    <GlassContainer
      className={twMerge('relative h-auto  rounded-2xl px-3 py-2', className)}
    >
      <div className="text-start text-base font-medium" data-testid="exchange-tooltip">
        {t(($) => $.tooltips.crossborderexport)}
        {isMobile ? '' : ':'}{' '}
        <b className="font-bold">
          {isHourly
            ? formatPower({ value: roundedNetFlow })
            : formatEnergy({ value: roundedNetFlow })}
        </b>
        <div>
          <div className={divClass}>
            <ZoneName zone={zoneFrom} textStyle="max-w-[165px]" />
            {isMobile ? <p className="ml-0.5">↓</p> : <p className="mx-2">→</p>}{' '}
            <ZoneName zone={zoneTo} textStyle="max-w-[165px]" />
          </div>
        </div>
        {t(($) => $.tooltips.carbonintensityexport)}:
        <div className="pt-1">
          {co2intensity > 0 ? (
            <div className="inline-flex items-center gap-x-1">
              <CarbonIntensityDisplay withSquare co2Intensity={co2intensity} />
            </div>
          ) : (
            <p className="text-neutral-400">
              {t(($) => $.tooltips.temporarilyUnavailable)}
            </p>
          )}
        </div>
      </div>
    </GlassContainer>
  );
}
