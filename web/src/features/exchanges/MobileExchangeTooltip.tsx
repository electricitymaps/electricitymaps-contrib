import type { ReactElement } from 'react';

import { CarbonIntensityDisplay } from 'components/CarbonIntensityDisplay';
import { ZoneName } from 'components/ZoneName';
import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { ExchangeArrowData } from 'types';
import { TimeAverages } from 'utils/constants';
import { formatEnergy, formatPower } from 'utils/formatting';
import { timeAverageAtom } from 'utils/state/atoms';

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
  const zoneTo = key.split('->')[isExporting ? 1 : 0];
  const [timeAverage] = useAtom(timeAverageAtom);
  const isHourly = timeAverage === TimeAverages.HOURLY;

  return (
    <div className="text-start text-base font-medium">
      {__('tooltips.crossborderexport')}:
      <div>
        <div className="flex-col items-center pb-2">
          <ZoneName zone={zoneFrom} textStyle="max-w-[165px]" />{' '}
          <p className="ml-0.5">↓</p> <ZoneName zone={zoneTo} textStyle="max-w-[165px]" />
          <b className="font-bold">
            {isHourly ? formatPower(roundedNetFlow) : formatEnergy(roundedNetFlow)}
          </b>
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
