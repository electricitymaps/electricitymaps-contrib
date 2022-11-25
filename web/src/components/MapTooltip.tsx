import * as Portal from '@radix-ui/react-portal';
import { useAtom } from 'jotai';
import type { ReactElement } from 'react';

import useGetState from 'api/getState';
import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import { ZoneName } from 'components/ZoneName';
import { useTranslation } from 'translation/translation';
import { Mode } from 'utils/constants';
import { formatDate } from 'utils/formatting';
import {
  productionConsumptionAtom,
  selectedDatetimeIndexAtom,
  timeAverageAtom,
} from 'utils/state';

interface MapTooltipProperties {
  mousePositionX: number;
  mousePositionY: number;
  hoveredFeature: { featureId: string | number | undefined; zoneId: string };
}

const getTooltipPosition = (
  mousePositionX: number,
  mousePositionY: number,
  screenWidth: number,
  tooltipWidth: number,
  tooltipHeight: number
) => {
  const ToolTipFlipBoundaryX = tooltipWidth + 30;
  const ToolTipFlipBoundaryY = tooltipHeight - 40;
  const xOffset = 10;
  const yOffset = tooltipHeight - 40;

  const tooltipPosition = {
    x: mousePositionX + xOffset,
    y: mousePositionY - yOffset,
  };
  if (screenWidth - mousePositionX < ToolTipFlipBoundaryX) {
    tooltipPosition.x = mousePositionX - tooltipWidth;
  }
  if (mousePositionY < ToolTipFlipBoundaryY) {
    tooltipPosition.y = mousePositionY;
  }
  return tooltipPosition;
};

function TooltipInner({
  zoneData,
  date,
  zoneId,
}: {
  date: string;
  zoneId: string;
  zoneData: {
    co2intensity: number;
    co2intensityProduction: number;
    countryCode: string;
    fossilFuelRatio: number;
    fossilFuelRatioProduction: number;
    renewableRatio: number;
    renewableRatioProduction: number;
    stateDatetime: number;
  };
}) {
  const {
    co2intensity,
    co2intensityProduction,
    fossilFuelRatio,
    fossilFuelRatioProduction,
    renewableRatio,
    renewableRatioProduction,
  } = zoneData;
  const [currentMode] = useAtom(productionConsumptionAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;

  return (
    <div className="w-full p-4 text-center">
      <ZoneName zone={zoneId} textStyle="text-base" />
      <div className="flex self-start text-xs">{date}</div>
      <div className=" flex w-full flex-grow p-1 sm:pr-4">
        <div className="flex w-full  flex-grow flex-row content-between justify-between">
          <CarbonIntensitySquare
            co2intensity={isConsumption ? co2intensity : co2intensityProduction}
          />
          <div className="px-4">
            <CircularGauge
              name="Low-carbon"
              ratio={isConsumption ? fossilFuelRatio : fossilFuelRatioProduction}
            />
          </div>
          <CircularGauge
            name="Renewable"
            ratio={isConsumption ? renewableRatio : renewableRatioProduction}
          />
        </div>
      </div>
    </div>
  );
}

export default function MapTooltip(properties: MapTooltipProperties): ReactElement {
  const { mousePositionX, mousePositionY, hoveredFeature } = properties;
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [timeAverage] = useAtom(timeAverageAtom);
  const { data } = useGetState(timeAverage);
  const hoveredZoneData = data?.data?.zones[hoveredFeature.zoneId] ?? undefined;
  const zoneData = hoveredZoneData
    ? data?.data?.zones[hoveredFeature.zoneId][selectedDatetime]
    : undefined;

  const screenWidth = window.innerWidth;
  const tooltipWithDataPositon = getTooltipPosition(
    mousePositionX,
    mousePositionY,
    screenWidth,
    290,
    176
  );
  const emptyTooltipPosition = getTooltipPosition(
    mousePositionX,
    mousePositionY,
    screenWidth,
    176,
    80
  );
  const { i18n } = useTranslation();
  const formattedDate = formatDate(
    new Date(selectedDatetime),
    i18n.language,
    timeAverage
  );

  if (zoneData) {
    return (
      <Portal.Root className="absolute left-0 top-0 h-0 w-0">
        <div
          className="relative h-[176px] w-[276px] rounded border bg-white  text-sm drop-shadow-sm dark:border-0 dark:bg-gray-900"
          style={{ left: tooltipWithDataPositon.x, top: tooltipWithDataPositon.y }}
        >
          <div>
            <TooltipInner
              zoneData={zoneData}
              zoneId={hoveredFeature.zoneId}
              date={formattedDate}
            />
          </div>
        </div>
      </Portal.Root>
    );
  }
  return (
    <Portal.Root className="absolute left-0 top-0 h-0 w-0">
      <div
        className="relative h-[80px] w-[176px] rounded border bg-white p-3 text-center text-sm drop-shadow-sm dark:border-0 dark:bg-gray-900"
        style={{ left: emptyTooltipPosition.x, top: emptyTooltipPosition.y }}
      >
        <div>
          <ZoneName zone={hoveredFeature.zoneId} textStyle="text-base" />
          <div className="flex self-start text-xs">{formattedDate}</div>
          <p className="text-start">No data available</p>
        </div>
      </div>
    </Portal.Root>
  );
}
