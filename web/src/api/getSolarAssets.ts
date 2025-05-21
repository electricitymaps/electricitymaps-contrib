import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';

import { getHeaders } from './helpers';

const getSolarAssets = async (): Promise<any> => {
  const path: URL = new URL(
    'https://storage.googleapis.com/testing-gzipped-geojson/solar_assets.min.geojson.gz'
  );

  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  const response = await fetch(path, requestOptions);
  const result = await response.json();
  console.log('res123', result);
  if (response.ok) {
    return result;
  }

  throw new Error(await response.text());
};

const useGetSolarAssets = (): UseQueryResult<Record<string, unknown>> =>
  useQuery<Record<string, unknown>>({
    queryKey: ['solarAssets'],
    queryFn: getSolarAssets,
  });

export default useGetSolarAssets;
