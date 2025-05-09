import invariant from 'tiny-invariant';
import { TimeRange } from 'utils/constants';

export const ONE_MINUTE = 60 * 1000;
export const FIVE_MINUTES = 5 * ONE_MINUTE;
export const ONE_HOUR = 60 * ONE_MINUTE;

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
    import.meta.env.VITE_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN_V9,
    'VITE_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN_V9 is not defined in environment'
  );
  return String(import.meta.env.VITE_PUBLIC_ELECTRICITYMAP_PUBLIC_TOKEN_V9);
}

/**
 * Generates authorized headers for the app-backend.
 *
 * @param route The route to generate x-signature for. Has to be given without the base path.
 * For example. `/v5/state/hourly` is a valid route, but `http://localhost:8001/v5/state/yearly` is not.
 */
export async function getHeaders(route: URL): Promise<Headers> {
  const token = isUsingLocalEndpoint() ? 'development' : getToken();
  const timestamp = Date.now().toString();
  const signature = await sha256(`${token}${route.pathname}${timestamp}`);

  return new Headers({
    'x-request-timestamp': timestamp,
    'x-signature': signature,
    'Cache-Control': 'public,maxage=60',
  });
}

/**
 * @returns The base path for the app-backend. If the app is running on localhost, the local endpoint is used.
 * @see isUsingLocalEndpoint
 */
export function getBasePath() {
  return isUsingLocalEndpoint()
    ? 'http://127.0.0.1:8001'
    : 'https://app-backend.electricitymaps.com';
}

export function cacheBuster(): string {
  const currentDate = new Date();
  const minutes = currentDate.getMinutes();
  currentDate.setMinutes(minutes - (minutes % 5));
  currentDate.setSeconds(0);
  currentDate.setMilliseconds(0);

  return currentDate.toISOString();
}

export const QUERY_KEYS = {
  STATE: 'state',
  ZONE: 'zone',
  META: 'meta',
};
export function isValidDate(dateString: string) {
  if (Number.isNaN(Date.parse(dateString))) {
    throw new TypeError('Invalid date string: ' + dateString);
  }
  const oldestDatetimeToSupport = new Date('2017-01-01T00:00:00Z');
  const parsedDate = new Date(dateString);
  if (parsedDate > oldestDatetimeToSupport) {
    return true;
  }
  return false;
}

export const TIME_RANGE_TO_TIME_AVERAGE: Record<TimeRange, string> = {
  [TimeRange.H72]: 'hourly',
  [TimeRange.M3]: 'daily',
  [TimeRange.M12]: 'monthly',
  [TimeRange.ALL_MONTHS]: 'monthly',
  [TimeRange.ALL_YEARS]: 'yearly',
} as const;

export const TIME_RANGE_TO_BACKEND_PATH: Record<TimeRange, string> = {
  [TimeRange.H72]: 'hourly',
  [TimeRange.M3]: 'daily',
  [TimeRange.M12]: 'monthly',
  [TimeRange.ALL_MONTHS]: 'monthly_all',
  [TimeRange.ALL_YEARS]: 'yearly',
} as const;

export const getParameters = (
  shouldQueryHistorical: boolean | '' | undefined,
  targetDatetime?: string
) => {
  if (shouldQueryHistorical) {
    return `?targetDate=${targetDatetime}`;
  }
  return '';
};
