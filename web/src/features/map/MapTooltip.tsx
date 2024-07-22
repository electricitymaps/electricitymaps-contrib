import * as Portal from '@radix-ui/react-portal';
import useGetState from 'api/getState';
import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import EstimationBadge from 'components/EstimationBadge';
import NoDataBadge from 'components/NoDataBadge';
import OutageBadge from 'components/OutageBadge';
import { getSafeTooltipPosition } from 'components/tooltips/utilities';
import { ZoneName } from 'components/ZoneName';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { StateZoneData } from 'types';
import { Mode } from 'utils/constants';
import { formatDate } from 'utils/formatting';
import { getCarbonIntensity, getFossilFuelRatio, getRenewableRatio } from 'utils/helpers';
import {
  productionConsumptionAtom,
  selectedDatetimeIndexAtom,
  selectedDatetimeStringAtom,
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
  zoneData: StateZoneData | undefined;
}) {
  const hasZoneData = Boolean(zoneData);
  zoneData ??= {
    p: {
      ci: null,
      fr: null,
      rr: null,
    },
    c: {
      ci: null,
      fr: null,
      rr: null,
    },
  };
  const { e, o } = zoneData;

  const { t } = useTranslation();

  const currentMode = useAtomValue(productionConsumptionAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;
  const intensity = getCarbonIntensity(zoneData, isConsumption);
  const fossilFuelPercentage = getFossilFuelRatio(zoneData, isConsumption);
  const renewable = getRenewableRatio(zoneData, isConsumption);

  return (
    <div className="w-full text-center">
      <div className="p-3">
        <div className="flex flex-col">
          <div className="flex w-full flex-row justify-between">
            <ZoneName zone={zoneId} textStyle="font-medium text-base font-poppins" />
            <DataValidityBadge hasOutage={o} estimated={e} hasZoneData={hasZoneData} />
          </div>
          <div className="flex self-start text-sm text-neutral-600 dark:text-neutral-400">
            {date}
          </div>{' '}
        </div>
        <div className="flex w-full grow py-1 pt-4 sm:pr-2">
          <div className="flex w-full grow flex-row justify-around">
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
  hasZoneData,
}: {
  hasOutage?: boolean | null;
  estimated?: number | boolean | null;
  hasZoneData: boolean;
}) {
  const { t } = useTranslation();

  if (!hasZoneData) {
    return <NoDataBadge />;
  }
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
  const mousePosition = useAtomValue(mousePositionAtom);
  const hoveredZone = useAtomValue(hoveredZoneAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const timeAverage = useAtomValue(timeAverageAtom);
  const isMapMoving = useAtomValue(mapMovingAtom);
  const { i18n } = useTranslation();
  const { data } = useGetState();

  if (!hoveredZone || isMapMoving) {
    return null;
  }

  const { zoneId } = hoveredZone;

  const { x, y } = mousePosition;
  const zoneData = data?.data?.datetimes[selectedDatetimeString]?.z[zoneId];

  const screenWidth = window.innerWidth;
  const tooltipWithDataPositon = getSafeTooltipPosition(x, y, screenWidth, 361, 170);

  const formattedDate = formatDate(selectedDatetime.datetime, i18n.language, timeAverage);

  return (
    <Portal.Root className="absolute left-0 top-0 hidden h-0 w-0 md:block">
      <div
        className="pointer-events-none relative w-[361px] rounded-2xl border border-neutral-200 bg-white text-sm shadow-lg dark:border-gray-700 dark:bg-gray-900 "
        style={{ left: tooltipWithDataPositon.x, top: tooltipWithDataPositon.y }}
      >
        <TooltipInner zoneData={zoneData} zoneId={zoneId} date={formattedDate} />
      </div>
    </Portal.Root>
  );
}
