import { useQuery } from '@tanstack/react-query';
import { resolvePath } from 'react-router-dom';
import { REFETCH_INTERVAL_ONE_HOUR } from './helpers';

async function getVersion(): Promise<{ version: string }> {
  const response = await fetch(resolvePath('client-version.json').pathname).then(
    (response) => {
      return response.json();
    }
  );
  return { version: response.version };
}

export const useGetAppVersion = () =>
  useQuery<{ version: string }>([], async () => getVersion(), {
    refetchInterval: REFETCH_INTERVAL_ONE_HOUR,
    refetchOnWindowFocus: false,
    cacheTime: 0,
  });
