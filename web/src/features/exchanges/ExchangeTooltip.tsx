import {
  CarbonIntensityDisplay,
  OtherPercentageDisplay,
} from 'components/CarbonIntensityDisplay';
import GlassContainer from 'components/GlassContainer';
import { ZoneName } from 'components/ZoneName';
import { useAtomValue } from 'jotai';
import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import { twMerge } from 'tailwind-merge';
import { ExchangeArrowData } from 'types';
import { MapColorSource } from 'utils/constants';
import { formatEnergy, formatPower } from 'utils/formatting';
import { getZoneValueForColor } from 'utils/helpers';
import { isConsumptionAtom, isHourlyAtom, mapColorSourceAtom } from 'utils/state/atoms';

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
  const mapColorSource = useAtomValue(mapColorSourceAtom);
  const isConsumption = useAtomValue(isConsumptionAtom);
  const { key, netFlow } = exchangeData;
  const value = getZoneValueForColor(
    exchangeData.originZoneData,
    isConsumption,
    mapColorSource
  );

  const isExporting = netFlow > 0;
  const roundedNetFlow = Math.abs(Math.round(netFlow));
  const zoneFrom = key.split('->')[isExporting ? 0 : 1];
  const zoneTo = key.split('->')[isExporting ? 1 : 0];

  const divClass = `${isMobile ? 'flex-col' : 'flex'} items-center pb-2`;

  let translationKey;
  if (mapColorSource == MapColorSource.CARBON_INTENSITY) {
    translationKey = 'tooltips.carbonintensityexport';
  } else if (mapColorSource == MapColorSource.RENEWABLE_PERCENTAGE) {
    translationKey = 'tooltips.renewablepercentageexport';
  } else {
    throw new Error('Invalid map color source');
  }

  return (
    <GlassContainer
      className={twMerge('relative h-auto  rounded-2xl px-3 py-2', className)}
    >
      <div className="text-start text-base font-medium" data-testid="exchange-tooltip">
        {t('tooltips.crossborderexport')}
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
        {t(translationKey)}:
        <div className="pt-1">
          {value > 0 ? (
            <div className="inline-flex items-center gap-x-1">
              {mapColorSource == MapColorSource.CARBON_INTENSITY ? (
                <CarbonIntensityDisplay withSquare co2Intensity={value} />
              ) : (
                <OtherPercentageDisplay withSquare value={value} />
              )}
            </div>
          ) : (
            <p className="text-neutral-400">{t('tooltips.temporarilyUnavailable')}</p>
          )}
        </div>
      </div>
    </GlassContainer>
  );
}
