import useGetZone from 'api/getZone';
import LoadingOrError from 'components/LoadingOrError';
import { useAtom } from 'jotai';
import { Navigate, useParams } from 'react-router-dom';
import { timeAverageAtom } from 'utils/state';

export default function ZoneDetails(): JSX.Element {
  const { zoneId } = useParams();
  const [timeAverage] = useAtom(timeAverageAtom);
  const { isLoading, isError, error, data } = useGetZone(timeAverage, zoneId, {
    enabled: Boolean(zoneId),
  });

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
