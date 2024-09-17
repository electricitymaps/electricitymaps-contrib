import * as Portal from '@radix-ui/react-portal';
import Accordion from 'components/Accordion';
import { HorizontalDivider } from 'components/Divider';
import { getOffsetTooltipPosition } from 'components/tooltips/utilities';
import { useHeaderHeight } from 'hooks/headerHeight';
import { useAtom, useAtomValue } from 'jotai';
import { Factory, UtilityPole, X, Zap } from 'lucide-react';
import React, { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType, ZoneKey } from 'types';
import useResizeObserver from 'use-resize-observer';
import trackEvent from 'utils/analytics';
import { TrackEvent } from 'utils/constants';
import {
  dataSourcesCollapsedBarBreakdownAtom,
  displayByEmissionsAtom,
  isConsumptionAtom,
  isHourlyAtom,
} from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';

import { DataSources } from '../DataSources';
import { determineUnit } from '../graphUtils';
import useBarBreakdownChartData from '../hooks/useBarElectricityBreakdownChartData';
import useZoneDataSources from '../hooks/useZoneDataSources';
import { RoundedCard } from '../RoundedCard';
import BreakdownChartTooltip from '../tooltips/BreakdownChartTooltip';
import BarBreakdownEmissionsChart from './BarBreakdownEmissionsChart';
import BarElectricityBreakdownChart from './BarElectricityBreakdownChart';
import BySource from './elements/BySource';
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

  const {
    capacitySources,
    powerGenerationSources,
    emissionFactorSources,
    emissionFactorSourcesToProductionSources,
  } = useZoneDataSources();

  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const { ref, width: observerWidth = 0 } = useResizeObserver<HTMLDivElement>();
  const { t } = useTranslation();
  const isBiggerThanMobile = useBreakpoint('sm');
  const isHourly = useAtomValue(isHourlyAtom);
  const isConsumption = useAtomValue(isConsumptionAtom);
  const width = observerWidth + X_PADDING;

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

  const [dataSourcesCollapsedBarBreakdown, setDataSourcesCollapsedBarBreakdown] = useAtom(
    dataSourcesCollapsedBarBreakdownAtom
  );

  const headerHeight = useHeaderHeight();

  if (isLoading) {
    return null;
  }

  if (!currentZoneDetail) {
    return (
      <div className="text-md relative w-full" ref={ref}>
        <BySource className="opacity-40" />
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
    setTooltipData(null);
  };

  const showPowerSources = Boolean(powerGenerationSources?.length > 0);
  const showEmissionSources = Boolean(emissionFactorSources?.length > 0);
  const showCapacitySources = Boolean(capacitySources?.length > 0);

  const showDataSourceAccordion = Boolean(
    showCapacitySources || showPowerSources || showEmissionSources
  );

  return (
    <RoundedCard ref={ref}>
      <BySource
        hasEstimationPill={hasEstimationPill}
        estimatedPercentage={currentZoneDetail.estimatedPercentage}
        unit={graphUnit}
        estimationMethod={currentZoneDetail.estimationMethod}
      />
      {!displayByEmissions && (
        <CapacityLegend>
          {t('country-panel.graph-legends.installed-capacity')} ({graphUnit})
        </CapacityLegend>
      )}
      {tooltipData && (
        <Portal.Root className="pointer-events-none absolute left-0 top-0 z-50 h-full w-full  sm:h-0 sm:w-0">
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
            <button className="p-auto pointer-events-auto flex h-8 w-8 items-center justify-center rounded-full bg-white shadow dark:bg-gray-800 sm:hidden">
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
          isMobile={false}
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
          isMobile={false}
          graphUnit={graphUnit}
        />
      )}
      {showDataSourceAccordion && (
        <>
          <HorizontalDivider />
          <Accordion
            onOpen={() => {
              trackEvent(TrackEvent.DATA_SOURCES_CLICKED, {
                chart: 'bar-breakdown-chart',
              });
            }}
            title={t('data-sources.title')}
            className="text-md"
            isCollapsed={dataSourcesCollapsedBarBreakdown}
            setState={setDataSourcesCollapsedBarBreakdown}
          >
            <DataSources
              title={t('data-sources.capacity')}
              icon={<UtilityPole size={16} />}
              sources={capacitySources}
            />
            <DataSources
              title={t('data-sources.power')}
              icon={<Zap size={16} />}
              sources={powerGenerationSources}
            />
            <DataSources
              title={t('data-sources.emission')}
              icon={<Factory size={16} />}
              sources={emissionFactorSources}
              emissionFactorSourcesToProductionSources={
                emissionFactorSourcesToProductionSources
              }
            />
          </Accordion>
        </>
      )}
    </RoundedCard>
  );
}

export default BarBreakdownChart;
