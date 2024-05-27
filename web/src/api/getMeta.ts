import { useQuery } from '@tanstack/react-query';
import { getBasePath, QUERY_KEYS } from 'api/helpers';

export type callerLocation = [number, number] | null;

export interface Meta {
  features?: Record<string, boolean>;
  callerLocation?: callerLocation;
}

export async function getMeta(): Promise<Meta> {
  const path: URL = new URL(`/v8/${QUERY_KEYS.META}`, getBasePath());

  try {
    const response = await fetch(path);
    if (response.ok) {
      const data = await response.json();
      return data;
    }

    throw new Error(await response.text());
  } catch (error) {
    // If the request fails, we will return an empty object instead of throwing an error
    // as the is still functional without the data
    console.error(error);
    return {};
  }
}

export function useMeta(): Meta {
  return (
    useQuery<Meta>([QUERY_KEYS.META], async () => getMeta(), {
      suspense: true,
    }).data ?? {}
  );
}
