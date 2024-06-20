import * as Portal from '@radix-ui/react-portal';
import useGetState from 'api/getState';
import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import EstimationBadge from 'components/EstimationBadge';
import OutageBadge from 'components/OutageBadge';
import { getSafeTooltipPosition } from 'components/tooltips/utilities';
import { ZoneName } from 'components/ZoneName';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { StateZoneData } from 'types';
import { Mode } from 'utils/constants';
import { formatDate } from 'utils/formatting';
import { getCarbonIntensity, getFossilFuelRatio, getRenewableRatio } from 'utils/helpers';
import {
  productionConsumptionAtom,
  selectedDatetimeIndexAtom,
  timeAverageAtom,
} from 'utils/state/atoms';

import { hoveredZoneAtom, mapMovingAtom, mousePositionAtom } from './mapAtoms';

export function TooltipInner({
  zoneData,
  date,
  zoneId,
}: {
  date: string;
  zoneId: string;
  zoneData: StateZoneData;
}) {
  const { e, o } = zoneData;

  const { t } = useTranslation();

  const [currentMode] = useAtom(productionConsumptionAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;
  const intensity = getCarbonIntensity(zoneData, isConsumption);
  const fossilFuelPercentage = getFossilFuelRatio(zoneData, isConsumption);
  const renewable = getRenewableRatio(zoneData, isConsumption);

  return (
    <div className="w-full text-center">
      <div className="p-3">
        <div className="flex w-full flex-row justify-between">
          <div className="max-w-full truncate pl-2">
            <ZoneName zone={zoneId} textStyle="font-medium text-base font-poppins" />
            <div className="flex self-start text-sm text-neutral-600 dark:text-neutral-400">
              {date}
            </div>{' '}
          </div>
          <DataValidityBadge hasOutage={o} estimated={e} />
        </div>
        <div className="flex w-full flex-grow py-1 pt-4 sm:pr-2">
          <div className="flex w-full flex-grow flex-row justify-around">
            <CarbonIntensitySquare intensity={intensity} />
            <CircularGauge
              name={t('country-panel.lowcarbon')}
              ratio={fossilFuelPercentage}
            />
            <CircularGauge name={t('country-panel.renewable')} ratio={renewable} />
          </div>
        </div>
      </div>
    </div>
  );
}

function DataValidityBadge({
  hasOutage,
  estimated,
}: {
  hasOutage?: boolean | null;
  estimated?: number | boolean | null;
}) {
  const { t } = useTranslation();

  if (hasOutage) {
    return <OutageBadge />;
  }
  if (estimated === true) {
    return <EstimationBadge text={t('estimation-badge.fully-estimated')} />;
  }
  if (estimated && estimated > 0) {
    return (
      <EstimationBadge
        text={t(`estimation-card.aggregated_estimated.pill`, {
          percentage: estimated,
        })}
      />
    );
  }
  return null;
}

export default function MapTooltip() {
  const [mousePosition] = useAtom(mousePositionAtom);
  const [hoveredZone] = useAtom(hoveredZoneAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [timeAverage] = useAtom(timeAverageAtom);
  const [isMapMoving] = useAtom(mapMovingAtom);
  const { i18n, t } = useTranslation();
  const { data } = useGetState();

  if (!hoveredZone || isMapMoving) {
    return null;
  }

  const { x, y } = mousePosition;
  const zoneData =
    data?.data?.datetimes[selectedDatetime.datetimeString]?.z[hoveredZone.zoneId] ??
    undefined;

  const screenWidth = window.innerWidth;
  const tooltipWithDataPositon = getSafeTooltipPosition(x, y, screenWidth, 361, 170);
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
          className="pointer-events-none relative w-[361px] rounded-2xl border border-neutral-200 bg-white text-sm shadow-lg dark:border-gray-700 dark:bg-gray-900"
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
        className="pointer-events-none relative w-[176px] rounded border bg-zinc-50 p-3 text-center text-sm drop-shadow-sm dark:border dark:border-gray-700 dark:bg-gray-800"
        style={{ left: emptyTooltipPosition.x, top: emptyTooltipPosition.y }}
      >
        <div>
          <ZoneName zone={hoveredZone.zoneId} textStyle="font-medium" />
          <div className="flex self-start text-xs">{formattedDate}</div>
          <p className="text-start">{t('tooltips.noParserInfo')}</p>
        </div>
      </div>
    </Portal.Root>
  );
}
