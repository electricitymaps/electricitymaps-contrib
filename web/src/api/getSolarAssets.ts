import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { FeatureCollection, Point } from 'geojson';

import { getHeaders } from './helpers';

const getSolarAssets = async (): Promise<FeatureCollection<Point>> => {
  const path: URL = new URL(
    'https://storage.googleapis.com/testing-gzipped-geojson/solar_power_plants.geojson'
  );

  const requestOptions: RequestInit = {
    headers: await getHeaders(path),
  };

  const response = await fetch(path, requestOptions);
  const result = await response.json();
  if (response.ok) {
    return result;
  }

  throw new Error(await response.text());
};

const useGetSolarAssets = (): UseQueryResult<FeatureCollection<Point>> =>
  useQuery({
    queryKey: ['solarAssets'],
    queryFn: getSolarAssets,
  });

export default useGetSolarAssets;
