import * as Portal from '@radix-ui/react-portal';
import EstimationBadge from 'components/EstimationBadge';
import { getOffsetTooltipPosition } from 'components/tooltips/utilities';
import { useGetEstimationTranslation } from 'hooks/getEstimationTranslation';
import { useHeaderHeight } from 'hooks/headerHeight';
import { TFunction } from 'i18next';
import { useAtom, useAtomValue } from 'jotai';
import { CircleDashed, TrendingUpDown, X } from 'lucide-react';
import React, { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType, ZoneKey } from 'types';
import useResizeObserver from 'use-resize-observer';
import { Charts, EstimationMethods, TimeAverages } from 'utils/constants';
import {
  displayByEmissionsAtom,
  isConsumptionAtom,
  isHourlyAtom,
  productionConsumptionAtom,
  timeAverageAtom,
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

  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
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

  const [tooltipData, setTooltipData] = useState<{
    selectedLayerKey: ElectricityModeType | ZoneKey;
    x: number;
    y: number;
  } | null>(null);
  const headerHeight = useHeaderHeight();

  const titleText = useBarBreakdownChartTitle();
  const estimationMethod = currentZoneDetail?.estimationMethod;
  const pillText = useGetEstimationTranslation(
    'pill',
    estimationMethod,
    currentZoneDetail?.estimatedPercentage
  );

  if (isLoading) {
    return null;
  }

  if (!currentZoneDetail) {
    return (
      <div className="text-md relative w-full" ref={ref}>
        <ChartTitle className="opacity-40" id={Charts.BAR_BREAKDOWN_CHART} />
        <EmptyBarBreakdownChart
          height={height}
          width={width}
          overLayText={t('country-panel.noDataAtTimestamp')}
        />
      </div>
    );
  }

  const onMouseOver = (
    layerKey: ElectricityModeType | ZoneKey,
    event: React.MouseEvent
  ) => {
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
  };

  const onMouseOut = () => {
    if (!isMobile) {
      setTooltipData(null);
    }
  };

  return (
    <RoundedCard ref={ref}>
      <ChartTitle
        titleText={titleText}
        unit={graphUnit}
        badge={
          hasEstimationPill ? (
            <EstimationBadge
              text={pillText}
              Icon={
                estimationMethod === EstimationMethods.TSA ? CircleDashed : TrendingUpDown
              }
            />
          ) : undefined
        }
        id={Charts.BAR_BREAKDOWN_CHART}
      />
      {!displayByEmissions && isHourly && (
        <CapacityLegend>
          {t('country-panel.graph-legends.installed-capacity')} ({graphUnit})
        </CapacityLegend>
      )}
      {tooltipData && (
        <Portal.Root className="pointer-events-none absolute left-0 top-0 z-50 h-full w-full sm:h-0 sm:w-0">
          <div
            className="absolute mt-14 flex h-full w-full flex-col items-center gap-y-1 bg-black/20 sm:mt-auto sm:items-start"
            style={{
              left: tooltipData?.x,
              top: tooltipData?.y <= headerHeight ? headerHeight : tooltipData?.y,
            }}
          >
            <BreakdownChartTooltip
              selectedLayerKey={tooltipData?.selectedLayerKey}
              zoneDetail={currentZoneDetail}
              hasEstimationPill={hasEstimationPill}
            />
            <button
              onClick={() => setTooltipData(null)}
              className="p-auto pointer-events-auto flex h-8 w-8 items-center justify-center rounded-full bg-white shadow dark:bg-gray-800 sm:hidden"
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
    </RoundedCard>
  );
}

export const useBarBreakdownChartTitle = () => {
  const { t } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const [mixMode] = useAtom(productionConsumptionAtom);
  const dataType = displayByEmissions ? 'emissions' : mixMode;

  return getText(timeAverage, dataType, t);
};

export const getText = (
  timePeriod: TimeAverages,
  dataType: 'emissions' | 'production' | 'consumption',
  t: TFunction
) => {
  const translations = {
    hourly: {
      emissions: t('country-panel.by-source.emissions'),
      production: t('country-panel.by-source.electricity-production'),
      consumption: t('country-panel.by-source.electricity-consumption'),
    },
    default: {
      emissions: t('country-panel.by-source.total-emissions'),
      production: t('country-panel.by-source.total-electricity-production'),
      consumption: t('country-panel.by-source.total-electricity-consumption'),
    },
  };
  const period = timePeriod === TimeAverages.HOURLY ? 'hourly' : 'default';
  return translations[period][dataType];
};

export default BarBreakdownChart;
