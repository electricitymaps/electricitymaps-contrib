import { Capacitor } from '@capacitor/core';
import useGetZone from 'api/getZone';
import ApiButton from 'components/buttons/ApiButton';
import GlassContainer from 'components/GlassContainer';
import HorizontalDivider from 'components/HorizontalDivider';
import LoadingSpinner from 'components/LoadingSpinner';
import BarBreakdownChart from 'features/charts/bar-breakdown/BarBreakdownChart';
import { useAtomValue, useSetAtom } from 'jotai';
import { useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, useLocation, useParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { RouteParameters } from 'types';
import { Charts, SpatialAggregate } from 'utils/constants';
import { round } from 'utils/helpers';
import {
  displayByEmissionsAtom,
  selectedDatetimeStringAtom,
  spatialAggregateAtom,
  timeRangeAtom,
} from 'utils/state/atoms';

import AreaGraphContainer from './AreaGraphContainer';
import Attribution from './Attribution';
import DisplayByEmissionToggle from './DisplayByEmissionToggle';
import EstimationCard from './EstimationCard';
import MethodologyCard from './MethodologyCard';
import NoInformationMessage from './NoInformationMessage';
import { getHasSubZones, getZoneDataStatus, ZoneDataStatus } from './util';
import ZoneHeader from './ZoneHeader';
import { ZoneHeaderGauges } from './ZoneHeaderGauges';

export default function ZoneDetails(): JSX.Element {
  const { zoneId } = useParams<RouteParameters>();
  const timeRange = useAtomValue(timeRangeAtom);
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const setViewMode = useSetAtom(spatialAggregateAtom);
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const { data, isError, isLoading } = useGetZone();
  const { t } = useTranslation();
  const hasSubZones = getHasSubZones(zoneId);
  const isSubZone = zoneId ? zoneId.includes('-') : true;
  const zoneDataStatus = zoneId && getZoneDataStatus(zoneId, data);
  const selectedData = data?.zoneStates[selectedDatetimeString];
  const { estimationMethod, estimatedPercentage } = selectedData || {};
  const roundedEstimatedPercentage = round(estimatedPercentage ?? 0, 0);
  const hasEstimationPill =
    Boolean(estimationMethod) || Boolean(roundedEstimatedPercentage);

  useEffect(() => {
    if (hasSubZones === null) {
      return;
    }
    // When first hitting the map (or opening a zone from the search panel),
    // set the correct matching view mode (zone or country).
    if (hasSubZones && !isSubZone) {
      setViewMode(SpatialAggregate.COUNTRY);
    }
    if (!hasSubZones && isSubZone) {
      setViewMode(SpatialAggregate.ZONE);
    }
  }, [hasSubZones, isSubZone, setViewMode]);

  useScrollHashIntoView(isLoading);

  const datetimes = useMemo(
    () => Object.keys(data?.zoneStates || {})?.map((key) => new Date(key)),
    [data]
  );
  const zoneMessage = data?.zoneMessage;

  // We isolate the component which is independant of `selectedData`
  // in order to avoid re-rendering it needlessly
  const zoneDetailsContent = useMemo(
    () =>
      zoneId &&
      zoneDataStatus && (
        <ZoneDetailsContent
          isLoading={isLoading}
          isError={isError}
          zoneDataStatus={zoneDataStatus}
        >
          <BarBreakdownChart hasEstimationPill={hasEstimationPill} />
          {zoneDataStatus !== ZoneDataStatus.NO_INFORMATION && (
            <EstimationCard
              zoneKey={zoneId}
              zoneMessage={zoneMessage}
              estimatedPercentage={roundedEstimatedPercentage}
            />
          )}
          <ApiButton backgroundClasses="mt-3 mb-1" type="primary" />
          {zoneDataStatus === ZoneDataStatus.AVAILABLE && (
            <AreaGraphContainer
              datetimes={datetimes}
              timeRange={timeRange}
              displayByEmissions={displayByEmissions}
            />
          )}

          <MethodologyCard />
          <HorizontalDivider />
          <div className="flex items-center justify-between gap-2">
            <div className="text-sm font-semibold">{t('country-panel.forecastCta')}</div>
            <ApiButton size="sm" />
          </div>
          <Attribution zoneId={zoneId} />
        </ZoneDetailsContent>
      ),
    [
      zoneId,
      zoneDataStatus,
      isLoading,
      isError,
      hasEstimationPill,
      zoneMessage,
      roundedEstimatedPercentage,
      datetimes,
      timeRange,
      displayByEmissions,
      t,
    ]
  );

  if (!zoneId) {
    return <Navigate to="/map" replace state={{ preserveSearch: true }} />;
  }

  // TODO: App-backend should not return an empty array as "data" if the zone does not
  // exist.
  if (Array.isArray(data)) {
    return <Navigate to="/map" replace state={{ preserveSearch: true }} />;
  }

  const isIosCapacitor =
    Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'ios';
  return (
    <GlassContainer className="pointer-events-auto z-[21] flex h-full flex-col border-0 pb-2 pt-10 transition-all duration-500 sm:inset-3 sm:bottom-48 sm:h-auto sm:border sm:pt-0">
      <section className="h-full w-full">
        <ZoneHeader zoneId={zoneId} isEstimated={false} />
        <div
          id="panel-scroller"
          className={twMerge(
            // TODO: Can we set the height here without using calc and specific zone-header value?
            'h-full flex-1 overflow-y-scroll px-3 pt-2.5 sm:h-[calc(100%-64px)] sm:pb-4',
            isIosCapacitor ? 'pb-72' : 'pb-32'
          )}
        >
          <ZoneHeaderGauges zoneKey={zoneId} />
          {zoneDataStatus !== ZoneDataStatus.NO_INFORMATION && (
            <DisplayByEmissionToggle />
          )}
          {zoneDetailsContent}
        </div>
      </section>
    </GlassContainer>
  );
}

function ZoneDetailsContent({
  isLoading,
  isError,
  children,
  zoneDataStatus,
}: {
  isLoading: boolean;
  isError: boolean;
  children: React.ReactNode;
  zoneDataStatus: ZoneDataStatus;
}): JSX.Element {
  if (isLoading) {
    return (
      <div className="relative mt-[10vh]">
        <LoadingSpinner />
      </div>
    );
  }

  if (isError) {
    return (
      <div
        data-testid="no-parser-message"
        className={`flex h-full w-full items-center justify-center text-sm`}
      >
        🤖 Unknown server error 🤖
      </div>
    );
  }

  if (zoneDataStatus === ZoneDataStatus.NO_INFORMATION) {
    return <NoInformationMessage />;
  }

  return children as JSX.Element;
}

const useScrollHashIntoView = (isLoading: boolean) => {
  const { hash, pathname, search } = useLocation();
  const anchor = hash.toLowerCase();

  useEffect(() => {
    if (isLoading) {
      return;
    }

    const chartIds = Object.values<string>(Charts);
    const anchorId = anchor.slice(1).toLowerCase(); // remove leading #

    if (anchor && chartIds.includes(anchorId)) {
      const anchorElement = anchor ? document.querySelector(anchor) : null;
      if (anchorElement) {
        anchorElement.scrollIntoView({
          behavior: 'smooth',
          inline: 'nearest',
        });
      }
    } else {
      // If already scrolled to element, then reset scroll on re-navigation (i.e. clicking on new zone on map)
      const element = document.querySelector('#panel-scroller');
      if (element) {
        element.scrollTop = 0;
      }
    }
  }, [anchor, isLoading, pathname, search]);
};
