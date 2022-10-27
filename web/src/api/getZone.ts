import type { QueryFunctionContext } from '@tanstack/react-query';
import type { ZoneDetails } from 'types';
import invariant from 'tiny-invariant';
import { getHeaders, getBasePath } from './helpers';

interface ZoneParameters extends QueryFunctionContext {
  queryKey: [string, string | undefined];
}

interface ZoneResponse {
  data: ZoneDetails;
}

export default async function getZone({ queryKey }: ZoneParameters): Promise<ZoneDetails> {
  const [key, zoneId] = queryKey;

  invariant(zoneId, 'ZoneId is required');

  const path = `/v5/${key}?countryCode=${zoneId}`;
  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  const { data } = (await fetch(`${getBasePath()}/${path}`, requestOptions).then(async (response) =>
    response.json()
  )) as ZoneResponse;

  return data;
}
