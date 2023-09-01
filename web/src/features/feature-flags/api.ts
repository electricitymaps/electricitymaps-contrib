import { useQuery, type QueryClient } from '@tanstack/react-query';
import { QUERY_KEYS, getBasePath, getHeaders } from 'api/helpers';
import { FeatureFlags } from './types';

export async function getFeatureFlags(): Promise<FeatureFlags> {
  const path = '/feature-flags';
  const requestOptions: RequestInit = {
    method: 'GET',
    headers: await getHeaders(path),
  };

  try {
    const response = await fetch(`${getBasePath()}${path}`, requestOptions);
    if (response.ok) {
      const data = await response.json();
      return data;
    }

    throw new Error(await response.text());
  } catch (error) {
    // If the request fails, we will return an empty object instead of throwing an error
    // as the app might still be functional without feature flags
    console.log(error);
    return {};
  }
}

export function useFeatureFlags(): FeatureFlags {
  return (
    useQuery<FeatureFlags>([QUERY_KEYS.FEATURE_FLAGS], async () => getFeatureFlags(), {
      suspense: true,
    }).data || {}
  );
}

export function useFeatureFlag(name: string): boolean {
  const features = useFeatureFlags();

  return features?.[name] || false;
}
