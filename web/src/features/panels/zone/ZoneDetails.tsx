import { Capacitor } from '@capacitor/core';
import useGetZone from 'api/getZone';
import { CommercialApiButton } from 'components/buttons/CommercialApiButton';
import LoadingSpinner from 'components/LoadingSpinner';
import BarBreakdownChart from 'features/charts/bar-breakdown/BarBreakdownChart';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';
import { useEffect } from 'react';
import { Navigate, Route, Routes, useLocation, useParams } from 'react-router-dom';
import { twMerge } from 'tailwind-merge';
import { ZoneMessage } from 'types';
import {
  EstimationMethods,
  LeftPanelToggleOptions,
  SpatialAggregate,
} from 'utils/constants';
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
  const { zoneId } = useParams();
  const timeAverage = useAtomValue(timeAverageAtom);
  const setViewMode = useSetAtom(spatialAggregateAtom);
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const { data } = useGetZone();
  const isHourly = useAtomValue(isHourlyAtom);
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

  if (!zoneId) {
    return <Navigate to="/" replace />;
  }

  const zoneDataStatus = getZoneDataStatus(zoneId, data, timeAverage);

  const selectedData = data?.zoneStates[selectedDatetimeString];
  const { estimationMethod } = selectedData || {};
  const zoneMessage = data?.zoneMessage;
  const cardType = getCardType({ estimationMethod, zoneMessage, isHourly });
  const isIosCapacitor =
    Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'ios';
  return (
    <>
      <ZoneHeaderTitle zoneId={zoneId} />
      <div
        className={twMerge(
          'mb-3 h-full overflow-y-scroll px-3  pt-2 sm:h-full sm:pb-60',
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
        <ZoneDetailRoutes />
      </div>
    </>
  );
}

export function ZoneDetailRoutes() {
  return (
    <Routes>
      <Route index element={<ZoneDetailsContent />} />
      <Route path={LeftPanelToggleOptions.ELECTRICITY} element={<ZoneDetailsContent />} />
      <Route
        path={LeftPanelToggleOptions.EMISSIONS}
        element={<ZoneDetailsContent displayByEmissions />}
      />
    </Routes>
  );
}

const useScrollHashIntoView = (isLoading: boolean) => {
  const location = useLocation();
  useEffect(() => {
    const hash = parseHash(location.hash);
    const hashElement = hash ? document.querySelector(hash) : null;
    if (!isLoading && hashElement) {
      hashElement.scrollIntoView({
        behavior: 'smooth',
        inline: 'nearest',
      });
    }
  }, [location.hash, isLoading]);
};

// TODO(cady): Pass displayByEmissions as prop?
export function ZoneDetailsContent({
  displayByEmissions = false,
}: {
  displayByEmissions?: boolean;
}) {
  const { data, isError, isLoading } = useGetZone();
  const { zoneId } = useParams();
  const isMobile = useIsMobile();
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const [_, setDisplayByEmissions] = useAtom(displayByEmissionsAtom);
  const timeAverage = useAtomValue(timeAverageAtom);

  setDisplayByEmissions(displayByEmissions);

  useScrollHashIntoView(isLoading);

  // TODO: App-backend should not return an empty array as "data" if the zone does not
  // exist.
  if (!zoneId) {
    return <Navigate to="/" replace />;
  }

  // TODO(cady): break out a useEstimation hook?
  const zoneDataStatus = getZoneDataStatus(zoneId, data, timeAverage);
  const datetimes = Object.keys(data?.zoneStates || {})?.map((key) => new Date(key));
  const selectedData = data?.zoneStates[selectedDatetimeString];
  const { estimationMethod, estimatedPercentage } = selectedData || {};
  const hasEstimationPill = Boolean(estimationMethod) || Boolean(estimatedPercentage);

  // TODO(cady): reconsider where ZoneDetailsContentWrapper should live
  return (
    <ZoneDetailsContentWrapper
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
    </ZoneDetailsContentWrapper>
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

function ZoneDetailsContentWrapper({
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

const QUERY_DELIMITER = '?';

function parseHash(hash: string) {
  const queryIndex = hash.indexOf(QUERY_DELIMITER);
  return queryIndex > -1 ? hash.slice(0, queryIndex) : hash;
}
