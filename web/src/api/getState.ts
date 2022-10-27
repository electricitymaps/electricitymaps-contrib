import type { QueryFunctionContext } from '@tanstack/react-query';
import type { GridState } from 'types';
import { getBasePath, getHeaders } from './helpers';

interface StateParameters extends QueryFunctionContext {
  queryKey: [string];
}

interface StateResponse {
  data: GridState;
}

export default async function getState({ queryKey }: StateParameters): Promise<GridState> {
  const [key] = queryKey;

  const path = `/v5/${key}`;
  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  const { data } = (await fetch(`${getBasePath()}/${path}`, requestOptions).then(async (response) =>
    response.json()
  )) as StateResponse;

  return data;
}
