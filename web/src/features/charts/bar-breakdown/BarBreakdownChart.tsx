import * as Portal from '@radix-ui/react-portal';
import Accordion from 'components/Accordion';
import { getOffsetTooltipPosition } from 'components/tooltips/utilities';
import { max as d3Max, min as d3Min } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import Divider from 'features/panels/zone/Divider';
import { useCo2ColorScale } from 'hooks/theme';
import { IndustryIcon } from 'icons/industryIcon';
import { UtilityPoleIcon } from 'icons/utilityPoleIcon';
import { WindTurbineIcon } from 'icons/windTurbineIcon';
import { useAtom } from 'jotai';
import React, { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { HiXMark } from 'react-icons/hi2';
import { ElectricityModeType, ZoneDetail, ZoneKey } from 'types';
import useResizeObserver from 'use-resize-observer';
import trackEvent from 'utils/analytics';
import { TimeAverages, TrackEvent } from 'utils/constants';
import { formatCo2, formatEnergy, formatPower } from 'utils/formatting';
import {
  dataSourcesCollapsedBarBreakdown,
  displayByEmissionsAtom,
  productionConsumptionAtom,
  timeAverageAtom,
} from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';

import { DataSources } from '../DataSources';
import { determineUnit } from '../graphUtils';
import useBarBreakdownChartData from '../hooks/useBarElectricityBreakdownChartData';
import useZoneDataSources from '../hooks/useZoneDataSources';
import BreakdownChartTooltip from '../tooltips/BreakdownChartTooltip';
import BarBreakdownEmissionsChart from './BarBreakdownEmissionsChart';
import BarElectricityBreakdownChart from './BarElectricityBreakdownChart';
import BarElectricityExchangeChart from './BarElectricityExchangeChart';
import BarEmissionExchangeChart from './BarEmissionExchangeChart';
import { LABEL_MAX_WIDTH, PADDING_X } from './constants';
import BySource from './elements/BySource';
import EmptyBarBreakdownChart from './EmptyBarBreakdownChart';
import { getDataBlockPositions, useHeaderHeight } from './utils';

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
    exchangeHeight,
    isConsumption,
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
  const [timeAverage] = useAtom(timeAverageAtom);
  const [mixMode] = useAtom(productionConsumptionAtom);
  const width = observerWidth + X_PADDING;

  const [tooltipData, setTooltipData] = useState<{
    selectedLayerKey: ElectricityModeType | ZoneKey;
    x: number;
    y: number;
  } | null>(null);

  const headerHeight = useHeaderHeight();

  const maxCO2eqExport = d3Max(exchangeData ?? [], (d) => Math.max(0, -d.gCo2eq)) || 0;
  const maxCO2eqImport = d3Max(exchangeData ?? [], (d) => Math.max(0, d.gCo2eq));
  const maxCO2eqProduction = d3Max(productionData ?? [], (d) => d.gCo2eq);

  // in CO₂eq

  const co2Scale = useMemo(
    () =>
      scaleLinear()
        .domain([
          -maxCO2eqExport || 0,
          Math.max(maxCO2eqProduction || 0, maxCO2eqImport || 0),
        ])
        .range([0, width - LABEL_MAX_WIDTH - PADDING_X]),
    [maxCO2eqExport, maxCO2eqProduction, maxCO2eqImport, width]
  );

  const formatCO2Tick = (t: number) => {
    const maxValue = maxCO2eqProduction || 1;

    return formatCo2(t, maxValue);
  };

  const { productionY, exchangeY } = getDataBlockPositions(
    productionData?.length ?? 0,
    exchangeData ?? []
  );

  const co2ColorScale = useCo2ColorScale();

  const isHourly = timeAverage === TimeAverages.HOURLY;

  // Use the whole history to determine the min/max values in order to avoid
  // graph jumping while sliding through the time range.
  const [minPower, maxPower] = useMemo(() => {
    return [
      d3Min(
        Object.values(zoneDetails?.zoneStates ?? {}).map((zoneData) =>
          Math.min(
            -zoneData.maxStorageCapacity || 0,
            -zoneData.maxStorage || 0,
            -zoneData.maxExport || 0,
            -zoneData.maxExportCapacity || 0
          )
        )
      ) || 0,
      d3Max(
        Object.values(zoneDetails?.zoneStates ?? {}).map((zoneData) =>
          Math.max(
            zoneData.maxCapacity || 0,
            zoneData.maxProduction || 0,
            zoneData.maxDischarge || 0,
            zoneData.maxStorageCapacity || 0,
            zoneData.maxImport || 0,
            zoneData.maxImportCapacity || 0
          )
        )
      ) || 0,
    ];
  }, [zoneDetails]);

  // Power in MW
  const powerScale = scaleLinear()
    .domain([minPower, maxPower])
    .range([0, width - LABEL_MAX_WIDTH - PADDING_X]);

  const formatPowerTick = (t: number) => {
    // Use same unit as max value for tick with value 0
    if (t === 0) {
      const tickValue = isHourly ? formatPower(maxPower, 1) : formatEnergy(maxPower, 1);
      return tickValue.toString().replace(/[\d.]+/, '0');
    }
    return isHourly ? formatPower(t, 2) : formatEnergy(t, 2);
  };

  if (isLoading) {
    return null;
  }

  if (!currentZoneDetail) {
    return (
      <div className="relative w-full text-md" ref={ref}>
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
    _: ZoneDetail,
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

  const showPowerSources = Boolean(
    powerGenerationSources && powerGenerationSources.length > 0
  );
  const showEmissionSources = Boolean(
    emissionFactorSources && emissionFactorSources.length > 0
  );
  const showCapacitySources = Boolean(capacitySources && capacitySources.length > 0);

  const showDataSourceAccordion = Boolean(
    showCapacitySources || showPowerSources || showEmissionSources
  );

  const graphUnit = determineUnit(
    displayByEmissions,
    currentZoneDetail,
    mixMode,
    timeAverage,
    t
  );

  return (
    <div
      className="mt-4 rounded-2xl border border-neutral-200 px-4 pb-2 text-sm dark:border-gray-700"
      ref={ref}
    >
      <BySource
        hasEstimationPill={hasEstimationPill}
        estimatedPercentage={currentZoneDetail.estimatedPercentage}
        unit={graphUnit}
        estimationMethod={currentZoneDetail.estimationMethod}
      />
      {!displayByEmissions && (
        <div className="flex flex-row pt-2">
          <span className="mt-0.5 h-3 w-3 rounded-full bg-black/10 dark:bg-white/10"></span>
          <span className="pl-2 text-sm font-medium text-neutral-600 dark:text-gray-300">
            {t('country-panel.graph-legends.installed-capacity')} {graphUnit}
          </span>
        </div>
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
            <button className="p-auto pointer-events-auto flex h-8 w-8 items-center justify-center rounded-full bg-white shadow sm:hidden dark:bg-gray-800">
              <HiXMark size="24" />
            </button>
          </div>
        </Portal.Root>
      )}
      {displayByEmissions ? (
        <BarBreakdownEmissionsChart
          data={currentZoneDetail}
          productionData={productionData}
          onProductionRowMouseOver={onMouseOver}
          onProductionRowMouseOut={onMouseOut}
          width={width}
          height={height}
          isMobile={false}
          co2Scale={co2Scale}
          formatTick={formatCO2Tick}
          productionY={productionY}
        />
      ) : (
        <BarElectricityBreakdownChart
          currentData={currentZoneDetail}
          productionData={productionData}
          onProductionRowMouseOver={onMouseOver}
          onProductionRowMouseOut={onMouseOut}
          onExchangeRowMouseOver={onMouseOver}
          onExchangeRowMouseOut={onMouseOut}
          width={width}
          height={height}
          isMobile={false}
          formatTick={formatPowerTick}
          powerScale={powerScale}
          productionY={productionY}
        />
      )}
      {isConsumption &&
        (displayByEmissions ? (
          <BarEmissionExchangeChart
            height={exchangeHeight + 20}
            onExchangeRowMouseOut={onMouseOut}
            onExchangeRowMouseOver={onMouseOver}
            exchangeData={exchangeData}
            data={currentZoneDetail}
            width={width}
            co2Scale={co2Scale}
            formatTick={formatCO2Tick}
          />
        ) : (
          <BarElectricityExchangeChart
            height={exchangeHeight + 20}
            onExchangeRowMouseOut={onMouseOut}
            onExchangeRowMouseOver={onMouseOver}
            exchangeData={exchangeData}
            data={currentZoneDetail}
            width={width}
            powerScale={powerScale}
            formatTick={formatPowerTick}
            co2ColorScale={co2ColorScale}
            graphUnit={graphUnit}
          />
        ))}
      {showDataSourceAccordion && (
        <>
          <Divider />
          <div className="py-1">
            <Accordion
              onOpen={() => {
                trackEvent(TrackEvent.DATA_SOURCES_CLICKED, {
                  chart: 'bar-breakdown-chart',
                });
              }}
              title={t('data-sources.title')}
              className="text-md"
              isCollapsedAtom={dataSourcesCollapsedBarBreakdown}
            >
              <div>
                <DataSources
                  title={t('data-sources.capacity')}
                  icon={<UtilityPoleIcon />}
                  sources={capacitySources}
                />
                <DataSources
                  title={t('data-sources.power')}
                  icon={<WindTurbineIcon />}
                  sources={powerGenerationSources}
                />
                <DataSources
                  title={t('data-sources.emission')}
                  icon={<IndustryIcon />}
                  sources={emissionFactorSources}
                  emissionFactorSourcesToProductionSources={
                    emissionFactorSourcesToProductionSources
                  }
                />
              </div>
            </Accordion>
          </div>{' '}
        </>
      )}
    </div>
  );
}

export default BarBreakdownChart;
