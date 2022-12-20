import { CarbonIntensityDisplayWithSquare } from 'components/CarbonIntensity';
import { CountryFlag } from 'components/Flag';
import { MetricRatio } from 'components/MetricRatio';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import React from 'react';
import { renderToString } from 'react-dom/server';
import AreaGraphToolTipHeader from 'stories/tooltips/AreaGraphTooltipHeader';
import { getZoneName, useTranslation } from 'translation/translation';
import { ZoneDetail } from 'types';
import { modeColor, modeOrder, TimeAverages } from 'utils/constants';
import { formatCo2, formatPower } from 'utils/formatting';
import { displayByEmissionsAtom, timeAverageAtom } from 'utils/state/atoms';
import { getRatioPercent } from '../graphUtils';
import { getExchangeTooltipData, getProductionTooltipData } from '../tooltipCalculations';
import { InnerAreaGraphTooltipProps } from '../types';

function calculateTooltipContentData(
  selectedLayerKey: string,
  zoneDetail: ZoneDetail,
  displayByEmissions: boolean
) {
  const isExchange = !modeOrder.includes(selectedLayerKey);

  return isExchange
    ? getExchangeTooltipData(selectedLayerKey, zoneDetail, displayByEmissions)
    : getProductionTooltipData(selectedLayerKey, zoneDetail, displayByEmissions);
}

export default function BreakdownChartTooltip(props: InnerAreaGraphTooltipProps) {
  const { zoneDetail, selectedLayerKey } = props;
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const [timeAverage] = useAtom(timeAverageAtom);
  // If layer key is not a generation type, it is an exchange
  const isExchange = !modeOrder.includes(selectedLayerKey);

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
  capacity: number;
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
  storage?: number;
  production?: number;
}

export function BreakdownChartTooltipContent(
  props: BreakdownChartTooltipContentProperties
) {
  const {
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
  } = props;

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

  return (
    <div className="w-full rounded-md bg-white p-3 text-sm shadow-3xl sm:w-[410px]">
      <AreaGraphToolTipHeader
        squareColor={
          isExchange ? co2ColorScale(co2Intensity) : modeColor[selectedLayerKey]
        }
        datetime={datetime}
        timeAverage={timeAverage}
        title={isExchange ? getZoneName(selectedLayerKey) : __(selectedLayerKey)}
      />
      <div
        className="inline-flex flex-wrap items-center gap-x-1"
        dangerouslySetInnerHTML={{ __html: headline }}
      />
      <br />
      <MetricRatio value={usage} total={totalElectricity} format={formatPower} />
      {!displayByEmissions && (
        <React.Fragment>
          <br />
          {timeAverage === TimeAverages.HOURLY && (
            <>
              <br />
              {__('tooltips.utilizing')} <b>{getRatioPercent(usage, capacity)} %</b>{' '}
              {__('tooltips.ofinstalled')}
              <br />
              <MetricRatio value={usage} total={capacity} format={formatPower} />
              <br />
            </>
          )}
          <br />
          {__('tooltips.representing')}{' '}
          <b>{getRatioPercent(emissions, totalEmissions)} %</b>{' '}
          {__('tooltips.ofemissions')}
          <br />
          <MetricRatio value={emissions} total={totalEmissions} format={formatCo2} />
        </React.Fragment>
      )}
      {!displayByEmissions && (Number.isFinite(co2Intensity) || usage !== 0) && (
        <React.Fragment>
          <br />
          <br />
          {__('tooltips.withcarbonintensity')}
          <br />
          <div className="flex-wrap">
            <div className="inline-flex items-center gap-x-1">
              <CarbonIntensityDisplayWithSquare co2Intensity={co2Intensity} />
            </div>
            {!isExchange && (
              <small>
                {' '}
                ({'Source'}: {co2IntensitySource || '?'})
              </small>
            )}
          </div>
        </React.Fragment>
      )}
    </div>
  );
}
