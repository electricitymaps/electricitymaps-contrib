import useGetZone from 'api/getZone';
import BarBreakdownChart from 'features/charts/bar-breakdown/BarBreakdownChart';
import { useAtom } from 'jotai';
import { Navigate, useParams } from 'react-router-dom';
import { TimeAverages } from 'utils/constants';
import { displayByEmissionsAtom, timeAverageAtom } from 'utils/state/atoms';
import AreaGraphContainer from './AreaGraphContainer';
import Attribution from './Attribution';
import DisplayByEmissionToggle from './DisplayByEmissionToggle';
import Divider from './Divider';
import NoInformationMessage from './NoInformationMessage';
import { ZoneHeader } from './ZoneHeader';
import { ZoneDataStatus, getZoneDataStatus } from './util';

export default function ZoneDetails(): JSX.Element {
  const { zoneId } = useParams();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const { data, isError, isLoading } = useGetZone({
    enabled: Boolean(zoneId),
  });

  // TODO: App-backend should not return an empty array as "data" if the zone does not
  // exist.
  if (!zoneId || Array.isArray(data)) {
    return <Navigate to="/" replace />;
  }

  const zoneDataStatus = getZoneDataStatus(zoneId, data);

  const datetimes = Object.keys(data?.zoneStates || {})?.map((key) => new Date(key));
  return (
    <>
      <ZoneHeader
        zoneId={zoneId}
        data={data}
        isAggregated={timeAverage !== TimeAverages.HOURLY}
      />
      {zoneDataStatus !== ZoneDataStatus.NO_INFORMATION && <DisplayByEmissionToggle />}
      <div className="h-[calc(100%-290px)] overflow-y-scroll p-4 pt-2 pb-40">
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
