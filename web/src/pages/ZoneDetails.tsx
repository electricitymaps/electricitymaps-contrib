import useGetZone from 'api/getZone';
import LoadingOrError from 'components/LoadingOrError';
import type { ReactElement } from 'react';
import { Navigate } from 'react-router-dom';
import { TimeAverages } from 'types';

export default function ZoneDetailsPage({ zoneId }: { zoneId: string }): ReactElement {
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
