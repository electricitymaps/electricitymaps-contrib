import Head from 'components/Head';
import LoadingOrError from 'components/LoadingOrError';
import type { ReactElement } from 'react';
import { useQuery } from '@tanstack/react-query';
import getZone from 'api/getZone';
import { Navigate, useParams } from 'react-router-dom';

export default function ZonePanelPage(): ReactElement {
  const { zoneId } = useParams();

  const { isLoading, isError, error, data } = useQuery(['history/hourly', zoneId], getZone, {
    enabled: !!zoneId,
  });

  if (!zoneId) {
    return <Navigate to="/" replace />;
  }

  if (isLoading || isError) {
    return <LoadingOrError error={error as Error} />;
  }

  return (
    <>
      <Head title={zoneId} />
      <h1>{zoneId}</h1>
      <div>
        {data.zoneStates.map((x) => (
          <div key={x.stateDatetime}>
            {x.stateDatetime} : {x.co2intensity}
          </div>
        ))}{' '}
      </div>
    </>
  );
}
