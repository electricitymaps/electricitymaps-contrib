import * as Portal from '@radix-ui/react-portal';
import { getOffsetTooltipPosition } from 'components/tooltips/utilities';
import { useAtom } from 'jotai';
import React, { useState } from 'react';
import { HiXMark } from 'react-icons/hi2';
import { useTranslation } from 'translation/translation';
import { ElectricityModeType, ZoneDetail, ZoneKey } from 'types';
import { displayByEmissionsAtom } from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';
import { useReferenceWidthHeightObserver } from 'utils/viewport';
import useBarBreakdownChartData from '../hooks/useBarElectricityBreakdownChartData';
import BreakdownChartTooltip from '../tooltips/BreakdownChartTooltip';
import BarBreakdownEmissionsChart from './BarBreakdownEmissionsChart';
import BarElectricityBreakdownChart from './BarElectricityBreakdownChart';
import EmptyBarBreakdownChart from './EmptyBarBreakdownChart';
import BySource from './elements/BySource';

const X_PADDING = 9;

function BarBreakdownChart() {
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
  const { __ } = useTranslation();
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
          overLayText={__('country-panel.noDataAtTimestamp')}
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

  return (
    <div className="text-sm" ref={ref}>
      <BySource />
      {tooltipData && (
        <Portal.Root
          className="pointer-events-none absolute left-0 top-0 z-50 flex h-full w-full flex-col items-center gap-y-1 bg-black/20 p-2 pt-14 sm:block sm:h-0 sm:w-0 sm:p-0"
          style={{
            left: tooltipData?.x,
            top: tooltipData?.y,
          }}
        >
          <BreakdownChartTooltip
            selectedLayerKey={tooltipData?.selectedLayerKey}
            zoneDetail={currentZoneDetail}
          />
          <button className="p-auto pointer-events-auto flex h-8 w-8 items-center justify-center rounded-full bg-white shadow dark:bg-gray-900 sm:hidden">
            <HiXMark size="24" />
          </button>
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
    </div>
  );
}

export default BarBreakdownChart;
