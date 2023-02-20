import { CarbonIntensityDisplay } from 'components/CarbonIntensityDisplay';
import { ZoneName } from 'components/ZoneName';
import type { ReactElement } from 'react';
import { useTranslation } from 'translation/translation';
import { ExchangeArrowData } from 'types';
import { formatPower } from 'utils/formatting';

interface MobileExchangeTooltipProperties {
  exchangeData: ExchangeArrowData;
}

export default function MobileExchangeTooltip(
  properties: MobileExchangeTooltipProperties
): ReactElement {
  const { key, netFlow, co2intensity } = properties.exchangeData;
  const { __ } = useTranslation();
  const isExporting = netFlow > 0;
  const roundedNetFlow = Math.abs(Math.round(netFlow));
  const zoneFrom = key.split('->')[isExporting ? 0 : 1];
  const zoneTo = key.split('->')[!isExporting ? 0 : 1];

  return (
    <div className="text-start text-base font-medium">
      {__('tooltips.crossborderexport')}:
      <div>
        <div className="flex-col items-center pb-2">
          <ZoneName zone={zoneFrom} textStyle="max-w-[165px]" />{' '}
          <p className="ml-0.5">↓</p> <ZoneName zone={zoneTo} textStyle="max-w-[165px]" />
          <b className="font-bold">{formatPower(roundedNetFlow)}</b>
        </div>
      </div>
      {__('tooltips.carbonintensityexport')}:
      <div className="pt-1">
        {co2intensity > 0 && (
          <div className="inline-flex items-center gap-x-1">
            <CarbonIntensityDisplay withSquare co2Intensity={co2intensity} />
          </div>
        )}
      </div>
    </div>
  );
}
