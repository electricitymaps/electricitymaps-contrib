import * as Portal from '@radix-ui/react-portal';
import { useAtom } from 'jotai';

import useGetState from 'api/getState';
import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import { ZoneName } from 'components/ZoneName';
import { getSafeTooltipPosition } from 'components/tooltips/utilities';
import { useTranslation } from 'translation/translation';
import { StateZoneData } from 'types';
import { Mode } from 'utils/constants';
import { formatDate } from 'utils/formatting';
import {
  productionConsumptionAtom,
  selectedDatetimeIndexAtom,
  timeAverageAtom,
} from 'utils/state/atoms';
import { hoveredZoneAtom, mapMovingAtom, mousePositionAtom } from './mapAtoms';
import { getFossilFuelPercentage } from 'utils/helpers';

function TooltipInner({
  zoneData,
  date,
  zoneId,
}: {
  date: string;
  zoneId: string;
  zoneData: StateZoneData;
}) {
  const {
    co2intensity,
    co2intensityProduction,
    fossilFuelRatio,
    fossilFuelRatioProduction,
    renewableRatio,
    renewableRatioProduction,
  } = zoneData;
  const { __ } = useTranslation();

  const [currentMode] = useAtom(productionConsumptionAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;
  const fossilFuelPercentage = getFossilFuelPercentage(
    isConsumption,
    fossilFuelRatio,
    fossilFuelRatioProduction
  );
  return (
    <div className="w-full text-center">
      <div className="pl-2">
        <ZoneName zone={zoneId} textStyle="text-base font-medium" />
        <div className="flex self-start text-xs">{date}</div>{' '}
      </div>
      <div className="flex w-full flex-grow py-1 sm:pr-2">
        <div className="flex w-full flex-grow flex-row justify-around">
          <CarbonIntensitySquare
            intensity={isConsumption ? co2intensity : co2intensityProduction}
          />
          <div className="pl-2 pr-6">
            <CircularGauge
              name={__('country-panel.lowcarbon')}
              ratio={fossilFuelPercentage}
            />
          </div>
          <CircularGauge
            name={__('country-panel.renewable')}
            ratio={isConsumption ? renewableRatio : renewableRatioProduction}
          />
        </div>
      </div>
    </div>
  );
}

export default function MapTooltip() {
  const [mousePosition] = useAtom(mousePositionAtom);
  const [hoveredZone] = useAtom(hoveredZoneAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [timeAverage] = useAtom(timeAverageAtom);
  const [isMapMoving] = useAtom(mapMovingAtom);
  const { i18n, __ } = useTranslation();
  const { data } = useGetState();

  if (!hoveredZone || isMapMoving) {
    return null;
  }

  const { x, y } = mousePosition;
  const hoveredZoneData = data?.data?.zones[hoveredZone.zoneId] ?? undefined;
  const zoneData = hoveredZoneData
    ? data?.data?.zones[hoveredZone.zoneId][selectedDatetime.datetimeString]
    : undefined;

  const screenWidth = window.innerWidth;
  const tooltipWithDataPositon = getSafeTooltipPosition(x, y, screenWidth, 300, 170);
  const emptyTooltipPosition = getSafeTooltipPosition(x, y, screenWidth, 176, 70);

  const formattedDate = formatDate(
    new Date(selectedDatetime.datetimeString),
    i18n.language,
    timeAverage
  );

  if (zoneData) {
    return (
      <Portal.Root className="absolute left-0 top-0 hidden h-0 w-0 md:block">
        <div
          className="pointer-events-none relative w-[300px] rounded border bg-zinc-50 p-3  text-sm shadow-lg dark:border-0 dark:bg-gray-900"
          style={{ left: tooltipWithDataPositon.x, top: tooltipWithDataPositon.y }}
        >
          <div>
            <TooltipInner
              zoneData={zoneData}
              zoneId={hoveredZone.zoneId}
              date={formattedDate}
            />
          </div>
        </div>
      </Portal.Root>
    );
  }
  return (
    <Portal.Root className="absolute left-0 top-0 hidden h-0 w-0 md:block">
      <div
        className="pointer-events-none relative w-[176px] rounded border bg-zinc-50 p-3 text-center text-sm drop-shadow-sm dark:border-0 dark:bg-gray-900"
        style={{ left: emptyTooltipPosition.x, top: emptyTooltipPosition.y }}
      >
        <div>
          <ZoneName zone={hoveredZone.zoneId} textStyle="font-medium" />
          <div className="flex self-start text-xs">{formattedDate}</div>
          <p className="text-start">{__('tooltips.noParserInfo')}</p>
        </div>
      </div>
    </Portal.Root>
  );
}
