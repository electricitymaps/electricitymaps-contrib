import { ZoneName } from 'components/ZoneName';
import { useCo2ColorScale } from 'hooks/theme';
import type { ReactElement } from 'react';
import { useTranslation } from 'translation/translation';
import { ExchangeArrowData } from 'types';
import { formatPower } from 'utils/formatting';

export function CarbonIntensity({ intensity }: { intensity?: number }) {
  const co2ColorScale = useCo2ColorScale();

  return (
    <div className="flex h-3 items-center">
      <div
        className="mr-1 h-3 w-3"
        style={{ backgroundColor: co2ColorScale(intensity ?? 0) }}
      />
      <b className="flex items-center font-bold">{Math.round(intensity ?? 0) || '?'}</b>
      <p className="pl-0.5"> gCO₂eq/kWh</p>
    </div>
  );
}

interface ExchangeTooltipProperties {
  exchangeData: ExchangeArrowData;
}

export default function ExchangeTooltip(
  properties: ExchangeTooltipProperties
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
        <div className="flex items-center pb-2">
          <ZoneName zone={zoneFrom} textStyle="max-w-[165px]" /> <p className="mx-2">→</p>{' '}
          <ZoneName zone={zoneTo} textStyle="max-w-[165px]" />
          <b className="font-bold">: {formatPower(roundedNetFlow)}</b>
        </div>
      </div>
      {__('tooltips.carbonintensityexport')}:
      <div className="pt-1">
        {Boolean(co2intensity) && <CarbonIntensity intensity={co2intensity} />}
      </div>
    </div>
  );
}
