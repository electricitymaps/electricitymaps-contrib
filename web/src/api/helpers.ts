import invariant from 'tiny-invariant';

export const REFETCH_INTERVAL_FIVE_MINUTES = 5 * 60 * 1000;
export const REFETCH_INTERVAL_ONE_HOUR = 60 * 60 * 1000;

async function sha256(message: string): Promise<string> {
  const BASE = 16;
  const MAX_LENGTH = 2;
  const hashBuffer = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(message)
  );
  return [...new Uint8Array(hashBuffer)]
    .map((b) => b.toString(BASE).padStart(MAX_LENGTH, '0'))
    .join('');
}

/**
 * Use local endpoint only if ALL of the following conditions are true:
1. The app is running on localhost
2. The `remote` search param hasn't been explicitly set to true
3. Document domain has a non-empty value
 * @returns
 */
function isUsingLocalEndpoint(): boolean {
  const isDevelopmentMode = import.meta.env.DEV;
  const isTestMode = import.meta.env.MODE === 'testing';
  return (
    (isDevelopmentMode || isTestMode) && !window.location.href.includes('remote=true')
  );
}

function getToken(): string {
  invariant(
    import.meta.env.VITE_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN,
    'VITE_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN is not defined in environment'
  );
  return String(import.meta.env.VITE_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN);
}

/**
 * Generates authorized headers for the app-backend.
 *
 * @param route The route to generate x-signature for. Has to be given without the base path.
 * For example. `/v5/state/hourly` is a valid route, but `http://localhost:8001/v5/state/yearly` is not.
 */
export async function getHeaders(route: string): Promise<Headers> {
  const token = isUsingLocalEndpoint() ? 'development' : getToken();
  const timestamp = Date.now().toString();
  const signature = await sha256(`${token}${route}${timestamp}`);

  return new Headers({
    'electricitymap-token': token,
    'x-request-timestamp': timestamp,
    'x-signature': signature,
  });
}

/**
 * @returns The base path for the app-backend. If the app is running on localhost, the local endpoint is used.
 * @see isUsingLocalEndpoint
 */
export function getBasePath() {
  return isUsingLocalEndpoint()
    ? 'http://127.0.0.1:8001'
    : 'https://app-backend.electricitymap.org';
}

export const QUERY_KEYS = {
  STATE: 'state',
  ZONE: 'zone',
};
