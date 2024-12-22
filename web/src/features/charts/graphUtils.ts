import { bisectLeft } from 'd3-array';
import { ScaleTime, scaleTime } from 'd3-scale';
import { pointer } from 'd3-selection';
import { TFunction } from 'i18next';
import { CircleDashed, LucideIcon, TrendingUpDown } from 'lucide-react';
import { MouseEvent } from 'react';
import { ElectricityStorageType, GenerationType, Maybe, ZoneDetail } from 'types';
import { EstimationMethods, modeOrder } from 'utils/constants';
import { formatCo2, formatEnergy, formatPower } from 'utils/formatting';
import { round } from 'utils/helpers';

import { AreaGraphElement } from './types';

export const detectHoveredDatapointIndex = (
  event_: MouseEvent<SVGRectElement> | MouseEvent<SVGPathElement>,
  datetimes: Date[],
  timeScale: ScaleTime<number, number>,
  svgNode: SVGSVGElement
): number | null => {
  if (datetimes.length === 0) {
    return null;
  }
  const timeIntervalWidth = timeScale(datetimes[1]) - timeScale(datetimes[0]);

  const dx = event_.pageX
    ? event_.pageX - svgNode.getBoundingClientRect().left
    : pointer(event_)[0];
  const adjustedDx = dx - timeIntervalWidth / 2;
  const datetime = timeScale.invert(adjustedDx);

  // Find data point closest to

  let index = bisectLeft(datetimes, datetime);
  // Aligns the hovered point to the chart bar
  if (
    index > 0 &&
    datetime?.getTime() - datetimes[index - 1]?.getTime() <
      datetimes[index]?.getTime() - datetime?.getTime()
  ) {
    index -= 1;
  }
  if (index > datetimes.length - 1) {
    index = datetimes.length - 1;
  }
  return index;
};

// If in mobile mode, put the tooltip to the top of the screen for
// readability, otherwise float it depending on the marker position.
export const getTooltipPosition = (isMobile: boolean, marker: { x: number; y: number }) =>
  isMobile ? { x: 0, y: 0 } : marker;

export const noop = () => undefined;

export const getTimeScale = (
  width: number,
  startTime?: Date | null,
  endTime?: Date | null
) => {
  if (!startTime || !endTime) {
    return null;
  }
  return scaleTime()
    .domain([new Date(startTime), new Date(endTime)])
    .range([0, width]);
};

export const getStorageKey = (name: ElectricityStorageType): string | undefined => {
  switch (name) {
    case 'hydro storage': {
      return 'hydro';
    }
    case 'battery storage': {
      return 'battery';
    }
    default: {
      return undefined;
    }
  }
};

export const getGenerationTypeKey = (name: string): GenerationType | undefined =>
  modeOrder.includes(name as GenerationType) ? (name as GenerationType) : undefined;

/** Returns the total electricity that is available in the zone (e.g. production + discharge + imports) */
export const getTotalElectricityAvailable = (
  zoneData: ZoneDetail,
  isConsumption: boolean
) => {
  const totalDischarge = zoneData.totalDischarge ?? 0;
  const totalImport = zoneData.totalImport ?? 0;

  if (zoneData.totalProduction === null) {
    return Number.NaN;
  }

  return zoneData.totalProduction + totalDischarge + (isConsumption ? totalImport : 0);
};

/** Returns the total emissions that is available in the zone (e.g. production + discharge + imports) */
export const getTotalEmissionsAvailable = (
  zoneData: ZoneDetail,
  isConsumption: boolean
) => {
  const totalCo2Discharge = zoneData.totalCo2Discharge ?? 0;
  const totalCo2Import = zoneData.totalCo2Import ?? 0;

  if (zoneData.totalCo2Production === null) {
    return Number.NaN;
  }

  return (
    zoneData.totalCo2Production + totalCo2Discharge + (isConsumption ? totalCo2Import : 0)
  );
};

export const getNextDatetime = (datetimes: Date[], currentDate: Date) => {
  const index = datetimes.findIndex((d) => d?.getTime() === currentDate?.getTime());
  if (index === -1 || index === datetimes.length - 1) {
    return undefined;
  }
  return datetimes[index + 1];
};

export const determineUnit = (
  displayByEmissions: boolean,
  currentZoneDetail: ZoneDetail,
  isConsumption: boolean,
  isHourly: boolean,
  t: TFunction
) => {
  if (displayByEmissions) {
    return getUnit(
      formatCo2({ value: getTotalEmissionsAvailable(currentZoneDetail, isConsumption) }) +
        ' ' +
        t('ofCO2eq')
    );
  }

  return isHourly
    ? getUnit(
        formatPower({
          value: getTotalElectricityAvailable(currentZoneDetail, isConsumption),
        })
      )
    : getUnit(
        formatEnergy({
          value: getTotalElectricityAvailable(currentZoneDetail, isConsumption),
        })
      );
};
const GET_UNIT_REGEX = /\s+(.+)/;
const getUnit = (valueAndUnit: string | number) =>
  valueAndUnit.toString().match(GET_UNIT_REGEX)?.at(1) ?? '';

export const getRatioPercent = (value: Maybe<number>, total: Maybe<number>) => {
  // If both the numerator and denominator are zeros,
  // interpret the ratio as zero instead of NaN.
  if (value === 0 && total === 0) {
    return 0;
  }
  // TODO: The typeof check is only necessary for TypeScript to properly narrow the types.
  // Remove it once TypeScript can narrow the type using the Number.isFinite check.
  if (
    typeof value !== 'number' ||
    typeof total !== 'number' ||
    !Number.isFinite(value) ||
    !Number.isFinite(total) ||
    total === 0
  ) {
    return '?';
  }
  return Math.round((value / total) * 10_000) / 100;
};

export const getElectricityProductionValue = ({
  generationTypeCapacity,
  isStorage,
  generationTypeProduction,
  generationTypeStorage,
}: {
  generationTypeCapacity: Maybe<number>;
  isStorage: boolean;
  generationTypeProduction: Maybe<number>;
  generationTypeStorage: Maybe<number>;
}) => {
  const value = isStorage ? generationTypeStorage : generationTypeProduction;

  // If the value is not defined but the capacity
  // is zero, assume the value is also zero.
  if (!Number.isFinite(value) && generationTypeCapacity === 0) {
    return 0;
  }

  if (!isStorage) {
    return value;
  }

  // Handle storage scenarios
  if (generationTypeStorage === null || generationTypeStorage === undefined) {
    return null;
  }
  // Do not negate value if it is zero
  return generationTypeStorage === 0 ? 0 : -generationTypeStorage;
};

const analyzeChartData = (chartData: AreaGraphElement[]) => {
  let estimatedCount = 0;
  let tsaCount = 0;
  let estimatedTotal = 0;
  const total = chartData.length;
  for (const chartElement of chartData) {
    if (
      chartElement.meta.estimationMethod === EstimationMethods.TSA ||
      chartElement.meta.estimationMethod === EstimationMethods.FORECASTS_HIERARCHY
    ) {
      tsaCount++;
    }
    if (chartElement.meta.estimatedPercentage || chartElement.meta.estimationMethod) {
      estimatedCount++;
    }
    estimatedTotal += chartElement.meta.estimatedPercentage ?? 0;
  }
  const calculatedTotal = round(
    estimatedTotal / total || ((estimatedCount || tsaCount) / total) * 100,
    0
  );
  return {
    estimatedTotal: calculatedTotal,
    allTimeSlicerAverageMethod: tsaCount === total,
    allEstimated: estimatedCount === total,
    hasEstimation: estimatedCount > 0,
  };
};

export const getBadgeTextAndIcon = (
  chartData: AreaGraphElement[],
  t: TFunction
): { text?: string; icon?: LucideIcon } => {
  const { allTimeSlicerAverageMethod, allEstimated, hasEstimation, estimatedTotal } =
    analyzeChartData(chartData);

  if (estimatedTotal === 0) {
    return {};
  }

  if (estimatedTotal) {
    return {
      text: t('estimation-card.aggregated_estimated.pill', {
        percentage: estimatedTotal,
      }),
      icon: TrendingUpDown,
    };
  }

  if (allTimeSlicerAverageMethod) {
    return {
      text: t(`estimation-card.${EstimationMethods.TSA}.pill`),
      icon: CircleDashed,
    };
  }

  if (allEstimated) {
    return { text: t('estimation-badge.fully-estimated'), icon: TrendingUpDown };
  }

  if (hasEstimation) {
    return { text: t('estimation-badge.partially-estimated'), icon: TrendingUpDown };
  }
  return {};
};

export const extractLinkFromSource = (
  source: string,
  sourceToLinkMapping: {
    [key: string]: string;
  }
) => {
  const link = sourceToLinkMapping[source];
  if (link) {
    return link;
  }

  if (!source.includes('.')) {
    return null;
  }

  if (source.includes('http')) {
    return source;
  }

  // We on purpose don't use https due to some sources not supporting it (and the majority that does will automatically redirect anyway)
  return `http://${source}`;
};
