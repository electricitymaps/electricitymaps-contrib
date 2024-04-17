import * as Portal from '@radix-ui/react-portal';
import Accordion from 'components/Accordion';
import { getOffsetTooltipPosition } from 'components/tooltips/utilities';
import Divider from 'features/panels/zone/Divider';
import { IndustryIcon } from 'icons/industryIcon';
import { UtilityPoleIcon } from 'icons/utilityPoleIcon';
import { WindTurbineIcon } from 'icons/windTurbineIcon';
import { useAtom } from 'jotai';
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { HiXMark } from 'react-icons/hi2';
import { ElectricityModeType, ZoneDetail, ZoneKey } from 'types';
import trackEvent from 'utils/analytics';
import { dataSourcesCollapsed, displayByEmissionsAtom } from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';
import { useReferenceWidthHeightObserver } from 'utils/viewport';

import useBarBreakdownChartData from '../hooks/useBarElectricityBreakdownChartData';
import BreakdownChartTooltip from '../tooltips/BreakdownChartTooltip';
import BarBreakdownEmissionsChart from './BarBreakdownEmissionsChart';
import BarElectricityBreakdownChart from './BarElectricityBreakdownChart';
import { DataSources } from './DataSources';
import BySource from './elements/BySource';
import EmptyBarBreakdownChart from './EmptyBarBreakdownChart';

const X_PADDING = 9;

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
  const { ref, width } = useReferenceWidthHeightObserver(X_PADDING);
  const { t } = useTranslation();
  const isBiggerThanMobile = useBreakpoint('sm');

  const [tooltipData, setTooltipData] = useState<{
    selectedLayerKey: ElectricityModeType | ZoneKey;
    x: number;
    y: number;
  } | null>(null);

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

  const emissionData = [
    ...new Set(
      [
        ...Object.values(currentZoneDetail?.dischargeCo2IntensitySources || {}),
        ...Object.values(currentZoneDetail?.productionCo2IntensitySources || {}),
      ].flatMap((item) => item.split('; '))
    ),
  ]
    .filter((item) => !item.startsWith('assumes'))
    .sort();

  return (
    <div
      className="mt-4 rounded-2xl border border-neutral-200 px-4 pb-2 text-sm dark:border-gray-700"
      ref={ref}
    >
      <BySource
        hasEstimationPill={hasEstimationPill}
        estimatedPercentage={currentZoneDetail.estimatedPercentage}
      />
      {tooltipData && (
        <Portal.Root className="pointer-events-none absolute left-0 top-0 z-50 h-full w-full  sm:h-0 sm:w-0">
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
          currentData={currentZoneDetail}
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
      )}
      <Divider />
      <div className="py-1">
        <Accordion
          onClick={() => {
            trackEvent('Data Sources Clicked', { chart: 'bar-breakdown-chart' });
          }}
          title={t('data-sources.title')}
          className="text-md"
          isCollapsedAtom={dataSourcesCollapsed}
        >
          <div>
            {currentZoneDetail?.capacitySources && (
              <DataSources
                title="Installed capacity data"
                icon={<UtilityPoleIcon />}
                sources={[
                  ...GetSourceArrayFromDictionary(currentZoneDetail?.capacitySources),
                ]}
              />
            )}
            {currentZoneDetail?.source && (
              <DataSources
                title="Power generation data"
                icon={<WindTurbineIcon />}
                sources={currentZoneDetail?.source}
              />
            )}
            {emissionData && (
              <DataSources
                title="Emission factor data"
                icon={<IndustryIcon />}
                sources={emissionData}
              />
            )}
          </div>
        </Accordion>
      </div>
    </div>
  );
}

export default BarBreakdownChart;

function GetSourceArrayFromDictionary(sourceDict: {
  [key in ElectricityModeType]: string[] | null;
}): Set<string> {
  const sourcesWithoutDuplicates: Set<string> = new Set();
  if (sourceDict == null) {
    return sourcesWithoutDuplicates;
  }
  for (const key of Object.keys(sourceDict)) {
    const capacitySource = sourceDict?.[key as ElectricityModeType];
    if (capacitySource != null) {
      for (const source of capacitySource) {
        sourcesWithoutDuplicates.add(source);
      }
    }
  }
  return sourcesWithoutDuplicates;
}
