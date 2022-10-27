import Head from 'components/Head';
import LoadingOrError from 'components/LoadingOrError';
import type { ReactElement } from 'react';
import { useQuery } from '@tanstack/react-query';
import getState from 'api/getState';

export default function MapPage(): ReactElement {
  const { isLoading, isError, error, data } = useQuery(['state/hourly'], getState);
  if (isLoading || isError) {
    return <LoadingOrError error={error as Error} />;
  }

  return (
    <>
      <Head title="Vitamin" />
      <div className="m-2 grid min-h-screen grid-cols-[minmax(0,384px)] place-content-center gap-2 md:m-0 md:grid-cols-[repeat(2,minmax(0,384px))] xl:grid-cols-[repeat(3,384px)]">
        {Object.entries(data.countries).map(([zoneKey, zoneOverviews]) =>
          zoneOverviews.length > 0 ? <li key={zoneKey}>{zoneOverviews[0].co2intensity}</li> : undefined
        )}
      </div>
    </>
  );
}
