import * as Portal from '@radix-ui/react-portal';
import Accordion from 'components/Accordion';
import { getOffsetTooltipPosition } from 'components/tooltips/utilities';
import { useAtom } from 'jotai';
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { HiXMark } from 'react-icons/hi2';
import { ElectricityModeType, ZoneDetail, ZoneKey } from 'types';
import { displayByEmissionsAtom } from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';
import { useReferenceWidthHeightObserver } from 'utils/viewport';

import useBarBreakdownChartData from '../hooks/useBarElectricityBreakdownChartData';
import BreakdownChartTooltip from '../tooltips/BreakdownChartTooltip';
import BarBreakdownEmissionsChart from './BarBreakdownEmissionsChart';
import BarElectricityBreakdownChart from './BarElectricityBreakdownChart';
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

  console.log('source', currentZoneDetail?.source);
  console.log('capacitysources', currentZoneDetail?.capacitySources);
  console.log(
    'dischargeCo2IntensitySources',
    currentZoneDetail?.dischargeCo2IntensitySources
  );
  console.log(
    'productionCo2IntensitySources',
    currentZoneDetail?.productionCo2IntensitySources
  );

  const emissionDataNoSplitOnSemicolon = [
    ...new Set([
      ...Object.values(currentZoneDetail?.dischargeCo2IntensitySources),
      ...Object.values(currentZoneDetail?.productionCo2IntensitySources),
    ]),
  ];

  const emissionData = [
    ...new Set(emissionDataNoSplitOnSemicolon.flatMap((item) => item.split('; '))),
  ];

  return (
    <div className="text-sm" ref={ref}>
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
      <div className="pt-2">
        <Accordion title={t('data-sources.title')} className="text-md">
          <div className="py-2">
            {currentZoneDetail?.capacitySources && (
              <Source
                title="Installed capacity data"
                icon={<HiXMark />}
                sources={GetSourceArrayFromDictionary(currentZoneDetail?.capacitySources)}
              />
            )}
            {currentZoneDetail?.source && (
              <Source
                title="Power generation data"
                icon={<HiXMark />}
                sources={[currentZoneDetail?.source]}
              />
            )}
            {emissionData && (
              <Source
                title="Emission factor data and exchange data?"
                icon={<HiXMark />}
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
}): string[] {
  const sourceArray: string[] = [];
  if (sourceDict == null) {
    return sourceArray;
  }
  for (const key of Object.keys(sourceDict)) {
    const capacitySource = sourceDict?.[key as ElectricityModeType];
    if (capacitySource != null) {
      for (const source of capacitySource) {
        if (!sourceArray.includes(source)) {
          sourceArray.push(source);
        }
      }
    }
  }
  return sourceArray;
}

function Source({
  title,
  icon,
  sources,
}: {
  title: string;
  icon: React.ReactNode;
  sources: string[];
}) {
  return (
    <div className="flex flex-col pb-3">
      <div className="flex flex-row pb-1">
        <div className="pr-2">{icon}</div>
        <div className="text-sm font-semibold">{title}</div>
      </div>
      <div className="flex flex-col gap-2">
        {sources.map((source, index) => (
          <div key={index} className="text-xm">
            {source}
          </div>
        ))}
      </div>
    </div>
  );
}
