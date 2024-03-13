import { CarbonIntensityDisplay } from 'components/CarbonIntensityDisplay';
import { CountryFlag } from 'components/Flag';
import { MetricRatio } from 'components/MetricRatio';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { renderToString } from 'react-dom/server';
import { useTranslation } from 'react-i18next';
import { getZoneName } from 'translation/translation';
import { ElectricityModeType, Maybe, ZoneDetail } from 'types';
import { Mode, modeColor, TimeAverages } from 'utils/constants';
import { formatCo2, formatEnergy, formatPower } from 'utils/formatting';
import {
  displayByEmissionsAtom,
  productionConsumptionAtom,
  timeAverageAtom,
} from 'utils/state/atoms';

import { getGenerationTypeKey, getRatioPercent } from '../graphUtils';
import { getExchangeTooltipData, getProductionTooltipData } from '../tooltipCalculations';
import { InnerAreaGraphTooltipProps, LayerKey } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

function calculateTooltipContentData(
  selectedLayerKey: LayerKey,
  zoneDetail: ZoneDetail,
  displayByEmissions: boolean,
  mixMode: Mode
) {
  // If layer key is not a generation type, it is an exchange
  const isExchange = !getGenerationTypeKey(selectedLayerKey);

  return isExchange
    ? getExchangeTooltipData(selectedLayerKey, zoneDetail, displayByEmissions)
    : getProductionTooltipData(
        selectedLayerKey as ElectricityModeType,
        zoneDetail,
        displayByEmissions,
        mixMode
      );
}

export default function BreakdownChartTooltip({
  zoneDetail,
  selectedLayerKey,
}: InnerAreaGraphTooltipProps) {
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const [timeAverage] = useAtom(timeAverageAtom);
  const [mixMode] = useAtom(productionConsumptionAtom);

  if (!zoneDetail || !selectedLayerKey) {
    return null;
  }

  // If layer key is not a generation type, it is an exchange
  const isExchange = !getGenerationTypeKey(selectedLayerKey);

  const contentData = calculateTooltipContentData(
    selectedLayerKey,
    zoneDetail,
    displayByEmissions,
    mixMode
  );

  const { estimationMethod, stateDatetime, estimatedPercentage } = zoneDetail;
  const hasEstimationPill = estimationMethod != undefined || Boolean(estimatedPercentage);

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
      datetime={new Date(stateDatetime)}
      isExchange={isExchange}
      selectedLayerKey={selectedLayerKey}
      originTranslateKey={getOriginTranslateKey()}
      timeAverage={timeAverage}
      hasEstimationPill={hasEstimationPill}
      estimatedPercentage={estimatedPercentage}
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
  selectedLayerKey: LayerKey;
  co2IntensitySource?: string;
  storage?: Maybe<number>;
  production?: Maybe<number>;
  hasEstimationPill?: boolean;
  estimatedPercentage?: number;
  capacitySource?: string[] | null;
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
  hasEstimationPill,
  estimatedPercentage,
  capacitySource,
}: BreakdownChartTooltipContentProperties) {
  const { t } = useTranslation();
  const co2ColorScale = useCo2ColorScale();
  // Dynamically generate the translated headline HTML based on the exchange or generation type
  const percentageUsage = displayByEmissions
    ? getRatioPercent(emissions, totalEmissions)
    : getRatioPercent(usage, totalElectricity);
  const headline = isExchange
    ? t(originTranslateKey, {
        percentageUsage: percentageUsage.toString(),
        zoneName: getZoneName(zoneKey),
        selectedZoneName: getZoneName(selectedLayerKey),
        zoneFlag: renderToString(<CountryFlag className="shadow-3xl" zoneId={zoneKey} />),
        selectedZoneFlag: renderToString(
          <CountryFlag className="shadow-3xl" zoneId={selectedLayerKey} />
        ),
      }) // Eg: "7 % of electricity in Denmark is imported from Germany"
    : t(originTranslateKey, {
        percentageUsage: percentageUsage.toString(),
        zoneName: getZoneName(zoneKey),
        selectedLayerKey: t(selectedLayerKey),
        zoneFlag: renderToString(<CountryFlag className="shadow-3xl" zoneId={zoneKey} />),
      }); // Eg: "20 % of electricity in Denmark comes from biomass"
  const title = isExchange
    ? getZoneName(selectedLayerKey)
    : t(selectedLayerKey).charAt(0).toUpperCase() + t(selectedLayerKey).slice(1);
  return (
    <div className="w-full rounded-md bg-white p-3 text-sm shadow-3xl sm:w-[410px] dark:border dark:border-gray-700 dark:bg-gray-800">
      <AreaGraphToolTipHeader
        squareColor={
          isExchange
            ? co2ColorScale(co2Intensity)
            : modeColor[selectedLayerKey as ElectricityModeType]
        }
        datetime={datetime}
        timeAverage={timeAverage}
        title={title}
        hasEstimationPill={isExchange ? false : hasEstimationPill}
        estimatedPercentage={estimatedPercentage}
        productionSource={isExchange ? undefined : selectedLayerKey}
      />
      <div
        className="inline-flex flex-wrap items-center gap-x-1"
        dangerouslySetInnerHTML={{ __html: headline }}
      />
      <br />
      {displayByEmissions && (
        <MetricRatio
          value={emissions}
          total={totalEmissions}
          format={formatCo2}
          label={t('ofCO2eq')}
          useTotalUnit
        />
      )}

      {!displayByEmissions && (
        <>
          <MetricRatio
            value={usage}
            total={totalElectricity}
            format={timeAverage === TimeAverages.HOURLY ? formatPower : formatEnergy}
          />
          <br />
          {timeAverage === TimeAverages.HOURLY && (
            <>
              <br />
              {t('tooltips.utilizing')} <b>{getRatioPercent(usage, capacity)} %</b>{' '}
              {t('tooltips.ofinstalled')}
              <br />
              <MetricRatio value={usage} total={(capacity ??= 0)} format={formatPower} />
              {capacitySource && (
                <small>
                  {' '}
                  ({t('country-panel.source')}: {capacitySource})
                </small>
              )}
              <br />
            </>
          )}
          <br />
          {t('tooltips.representing')}{' '}
          <b>{getRatioPercent(emissions, totalEmissions)} %</b>{' '}
          {t('tooltips.ofemissions')}
          <br />
          <MetricRatio
            value={emissions}
            total={totalEmissions}
            format={formatCo2}
            label={t('ofCO2eq')}
            useTotalUnit
          />
        </>
      )}
      {!displayByEmissions && (Number.isFinite(co2Intensity) || usage !== 0) && (
        <>
          <br />
          <br />
          {t('tooltips.withcarbonintensity')}
          <br />
          <div className="flex-wrap">
            <div className="inline-flex items-center gap-x-1">
              <CarbonIntensityDisplay withSquare co2Intensity={co2Intensity} />
            </div>
            {!isExchange && (
              <small>
                {' '}
                ({t('country-panel.source')}: {co2IntensitySource || '?'})
              </small>
            )}
          </div>
        </>
      )}
    </div>
  );
}
