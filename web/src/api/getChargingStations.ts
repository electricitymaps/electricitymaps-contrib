import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';

import { getHeaders } from './helpers';

const getChargingStations = async (): Promise<any> => {
  // invariant(zoneId, 'Zone ID is required');
  const path: URL = new URL(
    'https://developer.nrel.gov/api/alt-fuel-stations/v1.geojson?api_key=k3MSc53uMmlhpeMSrcGj87X5OKdS9TXNa6n7QVAf&access=public&fuel_type=ELEC&limit=200'
  );
  console.log('Hett');

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

// TODO: The frontend (graphs) expects that the datetimes in state are the same as in zone
// should we add a check for this?
const useGetChargingStations = (): UseQueryResult<any> => {
  // const zoneId = getChargingStationsFromPath();
  return useQuery<any>([''], async () => getChargingStations());
};

export default useGetChargingStations;
