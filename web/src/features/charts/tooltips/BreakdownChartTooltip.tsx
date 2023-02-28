import { CarbonIntensityDisplay } from 'components/CarbonIntensityDisplay';
import { CountryFlag } from 'components/Flag';
import { MetricRatio } from 'components/MetricRatio';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { renderToString } from 'react-dom/server';
import { getZoneName, useTranslation } from 'translation/translation';
import { ElectricityModeType, Maybe, ZoneDetail } from 'types';
import { TimeAverages, modeColor } from 'utils/constants';
import { formatCo2, formatPower } from 'utils/formatting';
import { displayByEmissionsAtom, timeAverageAtom } from 'utils/state/atoms';
import { getRatioPercent, getGenerationTypeKey } from '../graphUtils';
import { getExchangeTooltipData, getProductionTooltipData } from '../tooltipCalculations';
import { InnerAreaGraphTooltipProps, LayerKey } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

function calculateTooltipContentData(
  selectedLayerKey: LayerKey,
  zoneDetail: ZoneDetail,
  displayByEmissions: boolean
) {
  // If layer key is not a generation type, it is an exchange
  const isExchange = !getGenerationTypeKey(selectedLayerKey);

  return isExchange
    ? getExchangeTooltipData(selectedLayerKey, zoneDetail, displayByEmissions)
    : getProductionTooltipData(
        selectedLayerKey as ElectricityModeType,
        zoneDetail,
        displayByEmissions
      );
}

export default function BreakdownChartTooltip({
  zoneDetail,
  selectedLayerKey,
}: InnerAreaGraphTooltipProps) {
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const [timeAverage] = useAtom(timeAverageAtom);

  if (!zoneDetail || !selectedLayerKey) {
    return null;
  }

  // If layer key is not a generation type, it is an exchange
  const isExchange = !getGenerationTypeKey(selectedLayerKey);

  const contentData = calculateTooltipContentData(
    selectedLayerKey,
    zoneDetail,
    displayByEmissions
  );

  const getOriginTranslateKey = () => {
    if (isExchange) {
      if (contentData.isExport) {
        return displayByEmissions ? 'emissionsExportedTo' : 'electricityExportedTo';
      } else {
        return displayByEmissions ? 'emissionsImportedFrom' : 'electricityImportedFrom';
      }
    } else {
      if (contentData.isExport) {
        return displayByEmissions ? 'emissionsStoredUsing' : 'electricityStoredUsing';
      } else {
        return displayByEmissions ? 'emissionsComeFrom' : 'electricityComesFrom';
      }
    }
  };

  return (
    <BreakdownChartTooltipContent
      {...contentData}
      datetime={new Date(zoneDetail.stateDatetime)}
      isExchange={isExchange}
      selectedLayerKey={selectedLayerKey}
      originTranslateKey={getOriginTranslateKey()}
      timeAverage={timeAverage}
    ></BreakdownChartTooltipContent>
  );
}

interface BreakdownChartTooltipContentProperties {
  datetime: Date;
  usage: number;
  capacity: Maybe<number>;
  totalElectricity: number;
  totalEmissions: number;
  co2Intensity: number;
  timeAverage: TimeAverages;
  displayByEmissions: boolean;
  emissions: number;
  zoneKey: string;
  originTranslateKey: string;
  isExchange: boolean;
  selectedLayerKey: string;
  co2IntensitySource?: string;
  storage?: Maybe<number>;
  production?: Maybe<number>;
}

export function BreakdownChartTooltipContent({
  datetime,
  usage,
  totalElectricity,
  displayByEmissions,
  timeAverage,
  capacity,
  emissions,
  totalEmissions,
  co2Intensity,
  co2IntensitySource,
  zoneKey,
  originTranslateKey,
  isExchange,
  selectedLayerKey,
}: BreakdownChartTooltipContentProperties) {
  const { __ } = useTranslation();
  const co2ColorScale = useCo2ColorScale();
  // Dynamically generate the translated headline HTML based on the exchange or generation type
  const headline = isExchange
    ? __(
        originTranslateKey,
        getRatioPercent(usage, totalElectricity).toString(),
        getZoneName(zoneKey),
        getZoneName(selectedLayerKey),
        renderToString(<CountryFlag className="shadow-3xl" zoneId={zoneKey} />),
        renderToString(<CountryFlag className="shadow-3xl" zoneId={selectedLayerKey} />)
      ) // Eg: "7 % of electricity in Denmark is imported from Germany"
    : __(
        originTranslateKey,
        getRatioPercent(usage, totalElectricity).toString(),
        getZoneName(zoneKey),
        __(selectedLayerKey),
        renderToString(<CountryFlag className="shadow-3xl" zoneId={zoneKey} />)
      ); // Eg: "20 % of electricity in Denmark comes from biomass"
  const title = isExchange
    ? getZoneName(selectedLayerKey)
    : __(selectedLayerKey).charAt(0).toUpperCase() + __(selectedLayerKey).slice(1);
  return (
    <div className="w-full rounded-md bg-white p-3 text-sm shadow-3xl dark:bg-gray-900 sm:w-[410px]">
      <AreaGraphToolTipHeader
        squareColor={
          isExchange ? co2ColorScale(co2Intensity) : modeColor[selectedLayerKey]
        }
        datetime={datetime}
        timeAverage={timeAverage}
        title={title}
      />
      <div
        className="inline-flex flex-wrap items-center gap-x-1"
        dangerouslySetInnerHTML={{ __html: headline }}
      />
      <br />
      {displayByEmissions && (
        <MetricRatio value={emissions} total={totalEmissions} format={formatCo2} />
      )}

      {!displayByEmissions && (
        <>
          <MetricRatio value={usage} total={totalElectricity} format={formatPower} />
          <br />
          {timeAverage === TimeAverages.HOURLY && (
            <>
              <br />
              {__('tooltips.utilizing')} <b>{getRatioPercent(usage, capacity)} %</b>{' '}
              {__('tooltips.ofinstalled')}
              <br />
              <MetricRatio value={usage} total={(capacity ??= 0)} format={formatPower} />
              <br />
            </>
          )}
          <br />
          {__('tooltips.representing')}{' '}
          <b>{getRatioPercent(emissions, totalEmissions)} %</b>{' '}
          {__('tooltips.ofemissions')}
          <br />
          <MetricRatio value={emissions} total={totalEmissions} format={formatCo2} />
        </>
      )}
      {!displayByEmissions && (Number.isFinite(co2Intensity) || usage !== 0) && (
        <>
          <br />
          <br />
          {__('tooltips.withcarbonintensity')}
          <br />
          <div className="flex-wrap">
            <div className="inline-flex items-center gap-x-1">
              <CarbonIntensityDisplay withSquare co2Intensity={co2Intensity} />
            </div>
            {!isExchange && (
              <small>
                {' '}
                ({'Source'}: {co2IntensitySource || '?'})
              </small>
            )}
          </div>
        </>
      )}
    </div>
  );
}
