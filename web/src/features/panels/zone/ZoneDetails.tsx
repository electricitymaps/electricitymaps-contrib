import { Capacitor } from '@capacitor/core';
import useGetZone from 'api/getZone';
import { CommercialApiButton } from 'components/buttons/CommercialApiButton';
import LoadingSpinner from 'components/LoadingSpinner';
import BarBreakdownChart from 'features/charts/bar-breakdown/BarBreakdownChart';
import { useAtomValue, useSetAtom } from 'jotai';
import { useEffect } from 'react';
import { Navigate, useLocation, useNavigate, useParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { RouteParameters, ZoneMessage } from 'types';
import { Charts, EstimationMethods, SpatialAggregate } from 'utils/constants';
import {
  displayByEmissionsAtom,
  isHourlyAtom,
  selectedDatetimeStringAtom,
  spatialAggregateAtom,
  timeAverageAtom,
} from 'utils/state/atoms';
import { useIsMobile } from 'utils/styling';

import AreaGraphContainer from './AreaGraphContainer';
import Attribution from './Attribution';
import DisplayByEmissionToggle from './DisplayByEmissionToggle';
import EstimationCard from './EstimationCard';
import MethodologyCard from './MethodologyCard';
import NoInformationMessage from './NoInformationMessage';
import { getHasSubZones, getZoneDataStatus, ZoneDataStatus } from './util';
import { ZoneHeaderGauges } from './ZoneHeaderGauges';
import ZoneHeaderTitle from './ZoneHeaderTitle';

export default function ZoneDetails(): JSX.Element {
  const { zoneId } = useParams<RouteParameters>();
  const timeAverage = useAtomValue(timeAverageAtom);
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const setViewMode = useSetAtom(spatialAggregateAtom);
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const { data, isError, isLoading } = useGetZone();
  const isHourly = useAtomValue(isHourlyAtom);
  const isMobile = useIsMobile();
  const hasSubZones = getHasSubZones(zoneId);
  const isSubZone = zoneId ? zoneId.includes('-') : true;

  useEffect(() => {
    if (hasSubZones === null) {
      return;
    }
    // When first hitting the map (or opening a zone from the ranking panel),
    // set the correct matching view mode (zone or country).
    if (hasSubZones && !isSubZone) {
      setViewMode(SpatialAggregate.COUNTRY);
    }
    if (!hasSubZones && isSubZone) {
      setViewMode(SpatialAggregate.ZONE);
    }
  }, [hasSubZones, isSubZone, setViewMode]);

  useScrollHashIntoView(isLoading);

  if (!zoneId) {
    return <Navigate to="/map" replace state={{ preserveSearch: true }} />;
  }

  // TODO: App-backend should not return an empty array as "data" if the zone does not
  // exist.
  if (Array.isArray(data)) {
    return <Navigate to="/map" replace state={{ preserveSearch: true }} />;
  }

  const zoneDataStatus = getZoneDataStatus(zoneId, data, timeAverage);

  const datetimes = Object.keys(data?.zoneStates || {})?.map((key) => new Date(key));
  const selectedData = data?.zoneStates[selectedDatetimeString];
  const { estimationMethod, estimatedPercentage } = selectedData || {};
  const zoneMessage = data?.zoneMessage;
  const cardType = getCardType({ estimationMethod, zoneMessage, isHourly });
  const hasEstimationPill = Boolean(estimationMethod) || Boolean(estimatedPercentage);
  const isIosCapacitor =
    Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'ios';
  return (
    <>
      <ZoneHeaderTitle zoneId={zoneId} />
      <div
        id="panel-scroller"
        className={twMerge(
          'mb-3 h-full scroll-pt-5 overflow-y-scroll px-3 pt-2.5 sm:h-full sm:pb-60',
          isIosCapacitor ? 'pb-72' : 'pb-48'
        )}
      >
        {cardType != 'none' &&
          zoneDataStatus !== ZoneDataStatus.NO_INFORMATION &&
          zoneDataStatus !== ZoneDataStatus.AGGREGATE_DISABLED && (
            <EstimationCard
              cardType={cardType}
              estimationMethod={estimationMethod}
              zoneMessage={zoneMessage}
              estimatedPercentage={selectedData?.estimatedPercentage}
            />
          )}
        <ZoneHeaderGauges zoneKey={zoneId} />
        {zoneDataStatus !== ZoneDataStatus.NO_INFORMATION &&
          zoneDataStatus !== ZoneDataStatus.AGGREGATE_DISABLED && (
            <DisplayByEmissionToggle />
          )}
        <ZoneDetailsContent
          isLoading={isLoading}
          isError={isError}
          zoneDataStatus={zoneDataStatus}
        >
          <BarBreakdownChart hasEstimationPill={hasEstimationPill} />
          <CommercialApiButton backgroundClasses="mt-3 mb-1" type="link" />
          {zoneDataStatus === ZoneDataStatus.AVAILABLE && (
            <AreaGraphContainer
              datetimes={datetimes}
              timeAverage={timeAverage}
              displayByEmissions={displayByEmissions}
            />
          )}
          <MethodologyCard />
          <Attribution zoneId={zoneId} />
          {isMobile ? (
            <CommercialApiButton backgroundClasses="mt-3" />
          ) : (
            <div className="p-2" />
          )}
        </ZoneDetailsContent>
      </div>
    </>
  );
}

function getCardType({
  estimationMethod,
  zoneMessage,
  isHourly,
}: {
  estimationMethod?: EstimationMethods;
  zoneMessage?: ZoneMessage;
  isHourly: boolean;
}): 'estimated' | 'aggregated' | 'outage' | 'none' {
  if (
    (zoneMessage !== undefined &&
      zoneMessage?.message !== undefined &&
      zoneMessage?.issue !== undefined) ||
    estimationMethod === EstimationMethods.THRESHOLD_FILTERED
  ) {
    return 'outage';
  }
  if (!isHourly) {
    return 'aggregated';
  }
  if (estimationMethod) {
    return 'estimated';
  }
  return 'none';
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
    return <LoadingSpinner />;
  }

  if (isError) {
    return (
      <div
        data-test-id="no-parser-message"
        className={`flex h-full w-full items-center justify-center text-sm`}
      >
        🤖 Unknown server error 🤖
      </div>
    );
  }

  if (
    [
      ZoneDataStatus.NO_INFORMATION,
      ZoneDataStatus.AGGREGATE_DISABLED,
      ZoneDataStatus.FULLY_DISABLED,
    ].includes(zoneDataStatus)
  ) {
    return <NoInformationMessage status={zoneDataStatus} />;
  }

  return children as JSX.Element;
}

const useScrollHashIntoView = (isLoading: boolean) => {
  const { hash, pathname, search } = useLocation();
  const navigate = useNavigate();
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
  }, [anchor, isLoading, navigate, pathname, search]);
};
