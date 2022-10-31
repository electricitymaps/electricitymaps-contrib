import useGetZone from 'api/getZone';
import LoadingOrError from 'components/LoadingOrError';
import { Navigate, useParams } from 'react-router-dom';
import { TimeAverages } from 'types';

export default function ZoneDetails(): JSX.Element {
  const { zoneId } = useParams();

  const { isLoading, isError, error, data } = useGetZone(TimeAverages.HOURLY, zoneId, { enabled: Boolean(zoneId) });

  if (!zoneId) {
    return <Navigate to="/" replace />;
  }

  if (isLoading || isError) {
    return <LoadingOrError error={error as Error} />;
  }

  return (
    <div>
      {data.zoneStates.map((x) => (
        <div key={x.stateDatetime}>
          {x.stateDatetime} : {x.co2intensity}
        </div>
      ))}{' '}
    </div>
  );
}
