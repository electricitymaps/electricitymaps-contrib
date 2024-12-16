import { CarbonIntensityDisplay } from 'components/CarbonIntensityDisplay';
import { CountryFlag } from 'components/Flag';
import { MetricRatio } from 'components/MetricRatio';
import { useCo2ColorScale } from 'hooks/theme';
import { TFunction } from 'i18next';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { getZoneName } from 'translation/translation';
import { ElectricityModeType, Maybe, ZoneDetail } from 'types';
import { EstimationMethods, modeColor, TimeRange } from 'utils/constants';
import { formatCo2, formatEnergy, formatPower } from 'utils/formatting';
import { round } from 'utils/helpers';
import {
  displayByEmissionsAtom,
  isConsumptionAtom,
  isHourlyAtom,
  timeRangeAtom,
} from 'utils/state/atoms';

import { getGenerationTypeKey, getRatioPercent } from '../graphUtils';
import { getExchangeTooltipData, getProductionTooltipData } from '../tooltipCalculations';
import { InnerAreaGraphTooltipProps, LayerKey } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';

function calculateTooltipContentData(
  selectedLayerKey: LayerKey,
  zoneDetail: ZoneDetail,
  displayByEmissions: boolean,
  isConsumption: boolean
) {
  // If layer key is not a generation type, it is an exchange
  const isExchange = !getGenerationTypeKey(selectedLayerKey);

  return isExchange
    ? getExchangeTooltipData(selectedLayerKey, zoneDetail, displayByEmissions)
    : getProductionTooltipData(
        selectedLayerKey as ElectricityModeType,
        zoneDetail,
        displayByEmissions,
        isConsumption
      );
}

function Headline({
  isExchange,
  displayByEmissions,
  zoneKey,
  selectedLayerKey,
  percentageUsage,
  t,
  isExport,
}: {
  isExchange: boolean;
  displayByEmissions: boolean;
  zoneKey: string;
  selectedLayerKey: LayerKey;
  percentageUsage: string;
  t: TFunction;
  isExport: boolean;
}) {
  const availabilityKey = displayByEmissions
    ? 'emissionsAvailableIn'
    : 'electricityAvailableIn';

  const dataActionKey = getDataActionKey(isExchange, isExport, displayByEmissions);

  return (
    <div>
      <b>{percentageUsage} %</b> {t(availabilityKey)}
      <span className="mx-1 inline-flex">
        <CountryFlag className="shadow-3xl" zoneId={zoneKey} />
      </span>
      <b>{getZoneName(zoneKey)}</b> {t(dataActionKey)}
      {!isExchange && ` ${t(selectedLayerKey)}`}
      {isExchange && (
        <>
          <span className="mx-1 inline-flex">
            <CountryFlag className="shadow-3xl" zoneId={selectedLayerKey} />
          </span>
          <b>{getZoneName(selectedLayerKey)}</b>
        </>
      )}
    </div>
  );
}

function getDataActionKey(
  isExchange: boolean,
  isExport: boolean,
  displayByEmissions: boolean
) {
  if (isExchange) {
    if (isExport) {
      return displayByEmissions ? 'emissionsExportedTo' : 'electricityExportedTo';
    }
    return displayByEmissions ? 'emissionsImportedFrom' : 'electricityImportedFrom';
  } else {
    if (isExport) {
      return displayByEmissions ? 'emissionsStoredUsing' : 'electricityStoredUsing';
    }
    return 'comesFrom';
  }
}

export default function BreakdownChartTooltip({
  zoneDetail,
  selectedLayerKey,
}: InnerAreaGraphTooltipProps) {
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const timeRange = useAtomValue(timeRangeAtom);
  const isConsumption = useAtomValue(isConsumptionAtom);

  if (!zoneDetail || !selectedLayerKey) {
    return null;
  }

  // If layer key is not a generation type, it is an exchange
  const isExchange = !getGenerationTypeKey(selectedLayerKey);

  const contentData = calculateTooltipContentData(
    selectedLayerKey,
    zoneDetail,
    displayByEmissions,
    isConsumption
  );

  const { estimationMethod, stateDatetime, estimatedPercentage } = zoneDetail;
  const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
  const hasEstimationPill =
    estimationMethod != undefined || Boolean(roundedEstimatedPercentage);

  return (
    <BreakdownChartTooltipContent
      {...contentData}
      datetime={new Date(stateDatetime)}
      isExchange={isExchange}
      selectedLayerKey={selectedLayerKey}
      timeRange={timeRange}
      hasEstimationPill={hasEstimationPill}
      estimatedPercentage={roundedEstimatedPercentage}
      estimationMethod={estimationMethod}
    ></BreakdownChartTooltipContent>
  );
}

interface BreakdownChartTooltipContentProperties {
  datetime: Date;
  usage: number;
  capacity: number | null | undefined;
  totalElectricity: number;
  totalEmissions: number;
  co2Intensity: number;
  timeRange: TimeRange;
  displayByEmissions: boolean;
  emissions: number;
  zoneKey: string;
  isExchange: boolean;
  isExport: boolean;
  selectedLayerKey: LayerKey;
  co2IntensitySource?: string;
  storage?: Maybe<number>;
  production?: Maybe<number>;
  hasEstimationPill?: boolean;
  estimatedPercentage?: number;
  capacitySource?: string[] | null;
  estimationMethod?: EstimationMethods;
}

export function BreakdownChartTooltipContent({
  datetime,
  usage,
  totalElectricity,
  displayByEmissions,
  timeRange,
  capacity,
  emissions,
  isExport,
  totalEmissions,
  co2Intensity,
  co2IntensitySource,
  zoneKey,
  isExchange,
  selectedLayerKey,
  hasEstimationPill,
  estimatedPercentage,
  capacitySource,
  estimationMethod,
}: BreakdownChartTooltipContentProperties) {
  const { t } = useTranslation();
  const co2ColorScale = useCo2ColorScale();
  const isHourly = useAtomValue(isHourlyAtom);
  // Dynamically generate the translated headline HTML based on the exchange or generation type
  const percentageUsage = displayByEmissions
    ? getRatioPercent(emissions, totalEmissions)
    : getRatioPercent(usage, totalElectricity);

  const title = isExchange
    ? getZoneName(selectedLayerKey)
    : t(selectedLayerKey).charAt(0).toUpperCase() + t(selectedLayerKey).slice(1);
  return (
    <div className="w-full rounded-md bg-white p-3 text-sm shadow-3xl dark:border dark:border-gray-700 dark:bg-gray-800 sm:w-[410px]">
      <AreaGraphToolTipHeader
        squareColor={
          isExchange
            ? co2ColorScale(co2Intensity)
            : modeColor[selectedLayerKey as ElectricityModeType]
        }
        datetime={datetime}
        timeRange={timeRange}
        title={title}
        hasEstimationPill={isExchange ? false : hasEstimationPill}
        estimatedPercentage={estimatedPercentage}
        productionSource={isExchange ? undefined : selectedLayerKey}
        estimationMethod={estimationMethod}
      />
      <Headline
        isExchange={isExchange}
        displayByEmissions={displayByEmissions}
        percentageUsage={percentageUsage.toString()}
        zoneKey={zoneKey}
        selectedLayerKey={selectedLayerKey}
        t={t}
        isExport={isExport}
      />
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
        // Used to prevent browser translation crashes on edge, see #6809
        <div translate="no">
          <MetricRatio
            value={usage}
            total={totalElectricity}
            useTotalUnit
            format={isHourly ? formatPower : formatEnergy}
          />
          <br />
          {isHourly && (
            <>
              <br />
              {t('tooltips.utilizing')} <b>{getRatioPercent(usage, capacity)} %</b>{' '}
              {t('tooltips.ofinstalled')}
              <br />
              <MetricRatio
                value={usage}
                total={capacity}
                useTotalUnit
                format={formatPower}
              />
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
        </div>
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
