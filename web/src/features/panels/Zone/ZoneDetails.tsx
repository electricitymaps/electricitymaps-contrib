import useGetZone from 'api/getZone';
import { useAtom } from 'jotai';
import { Navigate, useParams } from 'react-router-dom';
import { timeAverageAtom } from 'utils/state';
import { ZoneHeader } from './ZoneHeader';

export default function ZoneDetails(): JSX.Element {
  const { zoneId } = useParams();
  const [timeAverage] = useAtom(timeAverageAtom);
  const { error, data, status } = useGetZone(timeAverage, zoneId, {
    enabled: Boolean(zoneId),
  });

  if (!zoneId) {
    return <Navigate to="/" replace />;
  }

  // TODO: Handle error state
  // TODO: Handle loading state nicely (let's keep country name in the header)
  console.error(error);
  console.log('I should do something with all this data', data);

  return (
    <div>
      <ZoneHeader zoneId={zoneId} date="November 9, 2022 at 8:00" isEstimated isAggregated />
      {status === 'loading' && 'Loading...'}
    </div>
  );
}
