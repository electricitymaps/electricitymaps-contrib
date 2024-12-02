import { bisectLeft } from 'd3-array';
import { ScaleTime, scaleTime } from 'd3-scale';
import { pointer } from 'd3-selection';
import { TFunction } from 'i18next';
import { CircleDashed, LucideIcon, TrendingUpDown } from 'lucide-react';
import { MouseEvent } from 'react';
import { ElectricityStorageType, GenerationType, Maybe, ZoneDetail } from 'types';
import { EstimationMethods, modeOrder } from 'utils/constants';
import { formatCo2, formatEnergy, formatPower } from 'utils/formatting';

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

export const getGenerationTypeKey = (name: string): GenerationType | undefined => {
  if (modeOrder.includes(name as GenerationType)) {
    return name as GenerationType;
  }

  return undefined;
};

/** Returns the total electricity that is available in the zone (e.g. production + discharge + imports) */
export function getTotalElectricityAvailable(
  zoneData: ZoneDetail,
  isConsumption: boolean
) {
  const totalDischarge = zoneData.totalDischarge ?? 0;
  const totalImport = zoneData.totalImport ?? 0;

  if (zoneData.totalProduction === null) {
    return Number.NaN;
  }

  return zoneData.totalProduction + totalDischarge + (isConsumption ? totalImport : 0);
}

/** Returns the total emissions that is available in the zone (e.g. production + discharge + imports) */
export function getTotalEmissionsAvailable(zoneData: ZoneDetail, isConsumption: boolean) {
  const totalCo2Discharge = zoneData.totalCo2Discharge ?? 0;
  const totalCo2Import = zoneData.totalCo2Import ?? 0;

  if (zoneData.totalCo2Production === null) {
    return Number.NaN;
  }

  return (
    zoneData.totalCo2Production + totalCo2Discharge + (isConsumption ? totalCo2Import : 0)
  );
}

export const getNextDatetime = (datetimes: Date[], currentDate: Date) => {
  const index = datetimes.findIndex((d) => d?.getTime() === currentDate?.getTime());
  if (index === -1 || index === datetimes.length - 1) {
    return undefined;
  }
  return datetimes[index + 1];
};

export function determineUnit(
  displayByEmissions: boolean,
  currentZoneDetail: ZoneDetail,
  isConsumption: boolean,
  isHourly: boolean,
  t: TFunction
) {
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
}

function getUnit(valueAndUnit: string | number) {
  const regex = /\s+(.+)/;
  const match = valueAndUnit.toString().match(regex);
  if (!match) {
    return '';
  }
  return match[1];
}

export function getRatioPercent(value: Maybe<number>, total: Maybe<number>) {
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
}

export function getElectricityProductionValue({
  generationTypeCapacity,
  isStorage,
  generationTypeProduction,
  generationTypeStorage,
}: {
  generationTypeCapacity: Maybe<number>;
  isStorage: boolean;
  generationTypeProduction: Maybe<number>;
  generationTypeStorage: Maybe<number>;
}) {
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
}

function analyzeChartData(chartData: AreaGraphElement[]) {
  let estimatedCount = 0;
  let tsaCount = 0;
  for (const chartElement of chartData) {
    if (chartElement.meta.estimationMethod === EstimationMethods.TSA) {
      tsaCount++;
    }
    if (chartElement.meta.estimatedPercentage || chartElement.meta.estimationMethod) {
      estimatedCount++;
    }
  }
  return {
    allTimeSlicerAverageMethod: tsaCount === chartData.length,
    allEstimated: estimatedCount === chartData.length,
    hasEstimation: estimatedCount > 0,
  };
}

export function getBadgeTextAndIcon(
  chartData: AreaGraphElement[],
  t: TFunction
): { text?: string; icon?: LucideIcon } {
  const { allTimeSlicerAverageMethod, allEstimated, hasEstimation } =
    analyzeChartData(chartData);
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
}

export function extractLinkFromSource(
  source: string,
  sourceToLinkMapping: {
    [key: string]: string;
  }
) {
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
}

export function hasSignificantEstimation(
  estimationMethod: EstimationMethods | undefined,
  estimatedPercentage: number | undefined
) {
  return (
    Boolean(estimationMethod) ||
    (estimatedPercentage != undefined && estimatedPercentage > 1)
  );
}
