import * as Portal from '@radix-ui/react-portal';
import useGetState from 'api/getState';
import { ValueSquare } from 'components/CarbonIntensitySquare';
import EstimationBadge from 'components/EstimationBadge';
import GlassContainer from 'components/GlassContainer';
import NoDataBadge from 'components/NoDataBadge';
import OutageBadge from 'components/OutageBadge';
import { TimeDisplay } from 'components/TimeDisplay';
import { getSafeTooltipPosition } from 'components/tooltips/utilities';
import ZoneGaugesWithCO2Square from 'components/ZoneGauges';
import { ZoneName } from 'components/ZoneName';
import { useColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { CircleDashed, TrendingUpDown } from 'lucide-react';
import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import { StateZoneData } from 'types';
import {
  EstimationMethods,
  isTSAModel,
  MapColorSource,
  mapColorSourceTranslationKeys,
  unitsByMapColorSource,
} from 'utils/constants';
import { round } from 'utils/helpers';
import { mapColorSourceAtom, selectedDatetimeStringAtom } from 'utils/state/atoms';

import { hoveredZoneAtom, mapMovingAtom, mousePositionAtom } from './mapAtoms';

const emptyZoneData: StateZoneData = {
  p: {},
  c: {},
  pr: null,
};

export const TooltipInner = memo(function TooltipInner({
  zoneData,
  zoneId,
}: {
  zoneId: string;
  zoneData?: StateZoneData;
}) {
  const mapColorSource = useAtomValue(mapColorSourceAtom);
  const colorScale = useColorScale();
  const hasZoneData = Boolean(zoneData);
  zoneData ??= emptyZoneData;
  const { em: estimationMethod, ep: estimationPercentage, o } = zoneData;

  const isPrice = mapColorSource === MapColorSource.ELECTRICITY_PRICE;

  return (
    <div className="flex w-full flex-col gap-2 py-3 text-center">
      <div className="flex flex-col px-3">
        <div className="flex w-full flex-row justify-between">
          <ZoneName zone={zoneId} textStyle="font-medium text-base font-poppins" />
          {!isPrice && (
            <DataValidityBadge
              hasOutage={Boolean(o)}
              estimatedMethod={estimationMethod}
              estimatedPercentage={round(estimationPercentage ?? 0, 0)}
              hasZoneData={hasZoneData}
            />
          )}
        </div>
        <TimeDisplay
          zoneId={zoneId}
          className="self-start text-sm text-neutral-600 dark:text-neutral-400"
        />
      </div>
      {isPrice ? (
        <ValueSquare
          value={zoneData.pr == null ? Number.NaN : zoneData.pr}
          colorScale={colorScale}
          unitRest={unitsByMapColorSource[mapColorSource].slice(1)}
          translationKey={mapColorSourceTranslationKeys[mapColorSource]}
          unitShort={unitsByMapColorSource[mapColorSource].slice(0, 1)}
        />
      ) : (
        <ZoneGaugesWithCO2Square zoneData={zoneData} classNames="justify-evenly" />
      )}
    </div>
  );
});

TooltipInner.displayName = 'TooltipInner';

export const DataValidityBadge = memo(function DataValidityBadge({
  hasOutage,
  estimatedMethod,
  estimatedPercentage,
  hasZoneData,
}: {
  hasOutage: boolean;
  estimatedMethod?: EstimationMethods | null;
  estimatedPercentage?: number | null;
  hasZoneData: boolean;
}) {
  const { t } = useTranslation();

  if (!hasZoneData) {
    return <NoDataBadge />;
  }
  if (hasOutage) {
    return <OutageBadge />;
  }
  if (estimatedMethod) {
    if (isTSAModel(estimatedMethod)) {
      return (
        <EstimationBadge
          text={t('estimation-card.ESTIMATED_TIME_SLICER_AVERAGE.pill')}
          Icon={CircleDashed}
          isPreliminary={true}
        />
      );
    }
    return (
      <EstimationBadge
        text={t(`estimation-card.${estimatedMethod}.pill`)}
        Icon={TrendingUpDown}
      />
    );
  }
  if (estimatedPercentage && estimatedPercentage > 0.5) {
    return (
      <EstimationBadge
        text={t(`estimation-card.aggregated_estimated.pill`, {
          percentage: estimatedPercentage,
        })}
        Icon={TrendingUpDown}
      />
    );
  }
  return null;
});

DataValidityBadge.displayName = 'DataValidityBadge';

export default function MapTooltip() {
  const mousePosition = useAtomValue(mousePositionAtom);
  const hoveredZone = useAtomValue(hoveredZoneAtom);
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const isMapMoving = useAtomValue(mapMovingAtom);
  const { data } = useGetState();

  if (!hoveredZone || isMapMoving) {
    return null;
  }

  const { zoneId } = hoveredZone;

  const { x, y } = mousePosition;
  const zoneData = data?.datetimes[selectedDatetimeString]?.z[zoneId];

  const screenWidth = window.innerWidth;
  const tooltipWithDataPositon = getSafeTooltipPosition(x, y, screenWidth, 361, 170);

  return (
    <Portal.Root className="absolute left-0 top-0 hidden h-0 w-0 md:block">
      <GlassContainer
        className="pointer-events-none relative w-[361px]"
        style={{ left: tooltipWithDataPositon.x, top: tooltipWithDataPositon.y }}
      >
        <TooltipInner zoneData={zoneData} zoneId={zoneId} />
      </GlassContainer>
    </Portal.Root>
  );
}
