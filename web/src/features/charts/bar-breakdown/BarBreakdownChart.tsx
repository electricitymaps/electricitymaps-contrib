import * as Portal from '@radix-ui/react-portal';
import useGetZone from 'api/getZone';
import EstimationBadge from 'components/EstimationBadge';
import { TimeDisplay } from 'components/TimeDisplay';
import { getOffsetTooltipPosition } from 'components/tooltips/utilities';
import EstimationCard from 'features/panels/zone/EstimationCard';
import { getZoneDataStatus, ZoneDataStatus } from 'features/panels/zone/util';
import { ZoneHeaderGauges } from 'features/panels/zone/ZoneHeaderGauges';
import { TFunction } from 'i18next';
import { useAtomValue } from 'jotai';
import { CircleDashed, TrendingUpDown, X } from 'lucide-react';
import React, { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { ElectricityModeType, RouteParameters, ZoneKey } from 'types';
import useResizeObserver from 'use-resize-observer';
import { Charts, isTSAModel, TimeRange } from 'utils/constants';
import getEstimationOrAggregationTranslation from 'utils/getEstimationTranslation';
import { round } from 'utils/helpers';
import {
  displayByEmissionsAtom,
  isConsumptionAtom,
  isHourlyAtom,
  productionConsumptionAtom,
  timeRangeAtom,
} from 'utils/state/atoms';
import { useBreakpoint, useIsMobile } from 'utils/styling';

import { ChartTitle } from '../ChartTitle';
import { determineUnit } from '../graphUtils';
import useBarBreakdownChartData from '../hooks/useBarElectricityBreakdownChartData';
import { RoundedCard } from '../RoundedCard';
import BreakdownChartTooltip from '../tooltips/BreakdownChartTooltip';
import BarBreakdownEmissionsChart from './BarBreakdownEmissionsChart';
import BarElectricityBreakdownChart from './BarElectricityBreakdownChart';
import CapacityLegend from './elements/CapacityLegend';
import EmptyBarBreakdownChart from './EmptyBarBreakdownChart';

const X_PADDING = 20;

function BarBreakdownChart({
  hasEstimationPill = false,
}: {
  hasEstimationPill: boolean;
}) {
  const {
    currentZoneDetail,
    zoneDetails,
    productionData,
    exchangeData,
    isLoading,
    height,
  } = useBarBreakdownChartData();
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const { ref, width: observerWidth = 0 } = useResizeObserver<HTMLDivElement>();
  const { t } = useTranslation();
  const isBiggerThanMobile = useBreakpoint('sm');
  const isHourly = useAtomValue(isHourlyAtom);
  const isConsumption = useAtomValue(isConsumptionAtom);
  const width = observerWidth + X_PADDING;
  const isMobile = useIsMobile();
  const graphUnit = useMemo(
    () =>
      currentZoneDetail &&
      determineUnit(displayByEmissions, currentZoneDetail, isConsumption, isHourly, t),
    [currentZoneDetail, displayByEmissions, isConsumption, isHourly, t]
  );
  const { zoneId } = useParams<RouteParameters>();
  const { data } = useGetZone();
  const zoneMessage = data?.zoneMessage;
  const zoneDataStatus = zoneId && getZoneDataStatus(zoneId, data);

  const [tooltipData, setTooltipData] = useState<{
    selectedLayerKey: ElectricityModeType | ZoneKey;
    x: number;
    y: number;
  } | null>(null);

  const titleText = useBarBreakdownChartTitle();
  const estimationMethod = currentZoneDetail?.estimationMethod;
  const estimatedPercentage = currentZoneDetail?.estimatedPercentage;
  const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
  const pillText = getEstimationOrAggregationTranslation(
    t,
    'pill',
    !isHourly,
    estimationMethod,
    currentZoneDetail?.estimatedPercentage
  );
  const isTSA = isTSAModel(estimationMethod);

  const onMouseOver = useCallback(
    (layerKey: ElectricityModeType | ZoneKey, event: React.MouseEvent) => {
      const { clientX, clientY } = event;

      const position = getOffsetTooltipPosition({
        mousePositionX: clientX || 0,
        mousePositionY: clientY || 0,
        tooltipHeight: displayByEmissions ? 190 : 360,
        isBiggerThanMobile,
      });

      setTooltipData({
        selectedLayerKey: layerKey,
        x: position.x,
        y: position.y,
      });
    },
    [displayByEmissions, isBiggerThanMobile]
  );

  const onMouseOut = useCallback(() => {
    if (!isMobile) {
      setTooltipData(null);
    }
  }, [isMobile]);

  if (isLoading || !zoneId) {
    return null;
  }

  if (!currentZoneDetail) {
    return (
      <RoundedCard ref={ref}>
        <ChartTitle className="opacity-40" id={Charts.ELECTRICITY_MIX_OVERVIEW_CHART} />
        <EmptyBarBreakdownChart
          height={height}
          width={width}
          overLayText={t('country-panel.noDataAtTimestamp')}
          isMobile={isMobile}
        />
      </RoundedCard>
    );
  }

  return (
    <RoundedCard ref={ref}>
      <ChartTitle
        titleText={titleText}
        subtitle={
          <TimeDisplay className="whitespace-nowrap text-xs text-neutral-600 dark:text-neutral-300" />
        }
        badge={
          hasEstimationPill ? (
            <EstimationBadge
              text={pillText}
              Icon={isTSA ? CircleDashed : TrendingUpDown}
              isPreliminary={isTSA}
            />
          ) : undefined
        }
        id={Charts.ELECTRICITY_MIX_OVERVIEW_CHART}
      />
      <div className="mb-4">
        <ZoneHeaderGauges zoneKey={currentZoneDetail.zoneKey} />
      </div>
      {!displayByEmissions && isHourly && (
        <CapacityLegend
          text={t('country-panel.graph-legends.installed-capacity')}
          unit={graphUnit}
        />
      )}
      {tooltipData && (
        <Portal.Root className="pointer-events-none absolute left-0 top-0 z-50 h-full w-full sm:h-0 sm:w-0">
          <div
            className="absolute mt-14 flex h-full w-full flex-col items-center gap-y-1 bg-black/20 sm:mt-auto sm:items-start"
            style={{
              left: tooltipData?.x,
              top: tooltipData?.y,
            }}
          >
            <BreakdownChartTooltip
              selectedLayerKey={tooltipData?.selectedLayerKey}
              zoneDetail={currentZoneDetail}
              hasEstimationPill={hasEstimationPill}
            />
            <button
              onClick={() => setTooltipData(null)}
              className="p-auto pointer-events-auto flex h-8 w-8 items-center justify-center rounded-full bg-white shadow dark:bg-neutral-800 sm:hidden"
            >
              <X />
            </button>
          </div>
        </Portal.Root>
      )}
      {displayByEmissions ? (
        <BarBreakdownEmissionsChart
          productionData={productionData}
          exchangeData={exchangeData}
          onProductionRowMouseOver={onMouseOver}
          onProductionRowMouseOut={onMouseOut}
          onExchangeRowMouseOver={onMouseOver}
          onExchangeRowMouseOut={onMouseOut}
          width={width}
          height={height}
          isMobile={isMobile}
        />
      ) : (
        <BarElectricityBreakdownChart
          data={zoneDetails}
          productionData={productionData}
          exchangeData={exchangeData}
          onProductionRowMouseOver={onMouseOver} // TODO(Viktor): change this to onMouseEnter to avoid repeated calls to the same function with the same data
          onProductionRowMouseOut={onMouseOut}
          onExchangeRowMouseOver={onMouseOver}
          onExchangeRowMouseOut={onMouseOut}
          width={width}
          height={height}
          isMobile={isMobile}
          graphUnit={graphUnit}
        />
      )}
      {zoneDataStatus !== ZoneDataStatus.NO_INFORMATION && (
        <EstimationCard
          zoneKey={zoneId}
          zoneMessage={zoneMessage}
          estimatedPercentage={roundedEstimatedPercentage}
        />
      )}
    </RoundedCard>
  );
}

export const useBarBreakdownChartTitle = () => {
  const { t } = useTranslation();
  const timeRange = useAtomValue(timeRangeAtom);
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const mixMode = useAtomValue(productionConsumptionAtom);
  const dataType = displayByEmissions ? 'emissions' : mixMode;

  return getText(timeRange, dataType, t);
};

export const getText = (
  timePeriod: TimeRange,
  dataType: 'emissions' | 'production' | 'consumption',
  t: TFunction
) => {
  const translations = {
    hourly: {
      emissions: t('country-panel.by-source.emissions'),
      production: t('country-panel.by-source.electricity-mix'),
      consumption: t('country-panel.by-source.electricity-mix'),
    },
    default: {
      emissions: t('country-panel.by-source.total-emissions'),
      production: t('country-panel.by-source.total-electricity-mix'),
      consumption: t('country-panel.by-source.total-electricity-mix'),
    },
  };
  const period = timePeriod === TimeRange.H72 ? 'hourly' : 'default';
  return translations[period][dataType];
};

export default BarBreakdownChart;
