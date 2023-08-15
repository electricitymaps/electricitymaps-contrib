import useGetZone from 'api/getZone';
import BarBreakdownChart from 'features/charts/bar-breakdown/BarBreakdownChart';
import { useAtom } from 'jotai';
import { useEffect } from 'react';
import { Navigate, useParams } from 'react-router-dom';
import { SpatialAggregate, TimeAverages } from 'utils/constants';
import {
  displayByEmissionsAtom,
  selectedDatetimeIndexAtom,
  spatialAggregateAtom,
  timeAverageAtom,
} from 'utils/state/atoms';
import AreaGraphContainer from './AreaGraphContainer';
import Attribution from './Attribution';
import DisplayByEmissionToggle from './DisplayByEmissionToggle';
import Divider from './Divider';
import NoInformationMessage from './NoInformationMessage';
import { ZoneHeaderGauges } from './ZoneHeaderGauges';
import { ZoneDataStatus, getHasSubZones, getZoneDataStatus } from './util';
import ZoneHeaderTitle from './ZoneHeaderTitle';

export default function ZoneDetails(): JSX.Element {
  const { zoneId } = useParams();
  if (!zoneId) {
    return <Navigate to="/" replace />;
  }
  const [timeAverage] = useAtom(timeAverageAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const [_, setViewMode] = useAtom(spatialAggregateAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const hasSubZones = getHasSubZones(zoneId);
  const isSubZone = zoneId ? zoneId.includes('-') : true;
  const { data, isError, isLoading } = useGetZone();
  // TODO: App-backend should not return an empty array as "data" if the zone does not
  // exist.
  if (Array.isArray(data)) {
    return <Navigate to="/" replace />;
  }

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
  }, []);

  const zoneDataStatus = getZoneDataStatus(zoneId, data);

  const datetimes = Object.keys(data?.zoneStates || {})?.map((key) => new Date(key));

  const selectedData = data?.zoneStates[selectedDatetime.datetimeString];
  const { estimationMethod } = selectedData || {};
  const isEstimated = estimationMethod !== undefined;
  const isAggregated = timeAverage !== TimeAverages.HOURLY;

  return (
    <>
      <ZoneHeaderTitle
        zoneId={zoneId}
        isAggregated={isAggregated}
        isEstimated={isEstimated}
      />
      <div className="h-[calc(100%-110px)] overflow-y-scroll p-4 pb-40 pt-2 sm:h-[calc(100%-130px)]">
        <ZoneHeaderGauges data={data} />
        {zoneDataStatus !== ZoneDataStatus.NO_INFORMATION && <DisplayByEmissionToggle />}
        <ZoneDetailsContent
          isLoading={isLoading}
          isError={isError}
          zoneDataStatus={zoneDataStatus}
        >
          <BarBreakdownChart />
          <Divider />
          {zoneDataStatus === ZoneDataStatus.AVAILABLE && (
            <AreaGraphContainer
              datetimes={datetimes}
              timeAverage={timeAverage}
              displayByEmissions={displayByEmissions}
            />
          )}
          <Attribution data={data} zoneId={zoneId} />
        </ZoneDetailsContent>
      </div>
    </>
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
      <div className={`flex h-full w-full items-center justify-center`}>
        <div className="z-50 h-[50px] w-[50px] bg-[url('/images/loading-icon.svg')] bg-[length:60px] bg-center bg-no-repeat dark:bg-[url('/images/loading-icon-darkmode.svg')]"></div>
      </div>
    );
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

  if (zoneDataStatus === ZoneDataStatus.NO_INFORMATION) {
    return <NoInformationMessage />;
  }

  return children as JSX.Element;
}
