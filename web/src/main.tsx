// Init CSS
import 'maplibre-gl/dist/maplibre-gl.css';
import 'react-spring-bottom-sheet/dist/style.css';
import './index.css';

import { Capacitor } from '@capacitor/core';
import * as Sentry from '@sentry/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from 'App';
import LoadingSpinner from 'components/LoadingSpinner';
import { zoneExists } from 'features/panels/zone/util';
import { lazy, StrictMode, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { HelmetProvider } from 'react-helmet-async';
import { I18nextProvider } from 'react-i18next';
import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
  useLocation,
  useParams,
  useSearchParams,
} from 'react-router-dom';
import i18n from 'translation/i18n';
import { RouteParameters } from 'types';
import { TimeRange } from 'utils/constants';
import { createConsoleGreeting } from 'utils/createConsoleGreeting';
import enableErrorsInOverlay from 'utils/errorOverlay';
import { getSentryUuid } from 'utils/getSentryUuid';
import { refetchDataOnHourChange } from 'utils/refetching';

const RankingPanel = lazy(() => import('features/panels/ranking-panel/RankingPanel'));
const ZoneDetails = lazy(() => import('features/panels/zone/ZoneDetails'));

const isProduction = import.meta.env.PROD;
if (isProduction) {
  Sentry.init({
    dsn: Capacitor.isNativePlatform()
      ? 'https://dfa9d3f487a738bcc1abc9329a5877c6@o192958.ingest.us.sentry.io/4507825555767296' // Capacitor DSN
      : 'https://bbe4fb6e5b3c4b96a1df95145a91e744@o192958.ingest.us.sentry.io/4504366922989568', // Web DSN
    tracesSampleRate: 0, // Disables tracing completely as we don't use it and sends a lot of data
    initialScope: (scope) => {
      scope.setUser({ id: getSentryUuid() }); // Set the user context with a random UUID for Sentry so we can correlate errors with users anonymously
      scope.setTag('browser.locale', window.navigator.language); // Set the language tag for Sentry to correlate errors with the user's language
      return scope;
    },
  });
}
/**
 * DevTools for Jotai which makes atoms appear in Redux Dev Tools.
 * Only enabled on import.meta.env.DEV
 */
// const AtomsDevtools = ({ children }: { children: JSX.Element }) => {
//   useAtomsDevtools('demo');
//   return children;
// };

createConsoleGreeting();

if (import.meta.env.DEV) {
  enableErrorsInOverlay();
}

const MAX_RETRIES = 1;
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: MAX_RETRIES,
      refetchOnWindowFocus: false,
      // by default data is cached and valid forever, as we handle invalidation ourselves
      gcTime: Number.POSITIVE_INFINITY,
      staleTime: Number.POSITIVE_INFINITY,
    },
  },
});

refetchDataOnHourChange(queryClient);

function TimeRangeGuardWrapper({ children }: { children: JSX.Element }) {
  const [searchParameters] = useSearchParams();
  const { urlTimeRange } = useParams<RouteParameters>();
  const location = useLocation();

  if (!urlTimeRange) {
    return (
      <Navigate
        to={`${location.pathname}/24h?${searchParameters}${location.hash}`}
        replace
      />
    );
  }

  const lowerCaseTimeRange = urlTimeRange.toLowerCase();

  if (!Object.values(TimeRange).includes(lowerCaseTimeRange as TimeRange)) {
    return (
      <Navigate
        to={`${location.pathname}/24h?${searchParameters}${location.hash}`}
        replace
      />
    );
  }

  if (urlTimeRange !== lowerCaseTimeRange) {
    return (
      <Navigate
        to={`${location.pathname.replace(
          urlTimeRange,
          lowerCaseTimeRange
        )}?${searchParameters}${location.hash}`}
        replace
      />
    );
  }

  return children;
}

export function ValidZoneIdGuardWrapper({ children }: { children: JSX.Element }) {
  const [searchParameters] = useSearchParams();
  const { zoneId } = useParams<RouteParameters>();
  if (!zoneId) {
    return <Navigate to={`/map/24h?${searchParameters}`} replace />;
  }

  // Sanitize the zone ID by removing any special characters except for hyphens and making it uppercase
  let sanitizedZoneId = zoneId.replaceAll(/[^\dA-Za-z-]/g, '').toUpperCase();

  // Remove trailing hyphens
  if (sanitizedZoneId.endsWith('-')) {
    sanitizedZoneId = sanitizedZoneId.slice(0, -1);
  }

  // Handle legacy Australian zone IDs
  if (sanitizedZoneId.startsWith('AUS')) {
    sanitizedZoneId = sanitizedZoneId.replace('AUS', 'AU');
  }

  if (zoneId !== sanitizedZoneId) {
    return <Navigate to={`/zone/${sanitizedZoneId}?${searchParameters}`} replace />;
  }

  // Only allow valid zone ids
  // TODO: This should redirect to a 404 page specifically for zones
  if (!zoneExists(sanitizedZoneId)) {
    return <Navigate to={`/map/24h?${searchParameters}`} replace />;
  }

  return children;
}

function HandleLegacyRoutes() {
  const [searchParameters] = useSearchParams();

  const page = (searchParameters.get('page') || 'map')
    .replace('country', 'zone')
    .replace('highscore', 'ranking');
  searchParameters.delete('page');

  const zoneId = searchParameters.get('countryCode');
  searchParameters.delete('countryCode');

  return (
    <Navigate
      to={{
        pathname: zoneId ? `/zone/${zoneId}` : `/${page}`,
        search: searchParameters.toString(),
      }}
    />
  );
}
const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      {
        path: '/',
        element: <HandleLegacyRoutes />,
      },
      {
        path: '/map',
        element: <Navigate to="/map/24h" replace />,
      },
      {
        path: '/zone',
        element: <Navigate to="/map/24h" replace />,
      },
      {
        path: '/map/:urlTimeRange?/:urlDatetime?',
        element: (
          <TimeRangeGuardWrapper>
            <RankingPanel />
          </TimeRangeGuardWrapper>
        ),
      },
      {
        path: '/zone/:zoneId/:urlTimeRange?/:urlDatetime?',
        element: (
          <ValidZoneIdGuardWrapper>
            <TimeRangeGuardWrapper>
              <Suspense fallback={<LoadingSpinner />}>
                <ZoneDetails />
              </Suspense>
            </TimeRangeGuardWrapper>
          </ValidZoneIdGuardWrapper>
        ),
      },
      {
        path: '*',
        element: (
          <Suspense fallback={<LoadingSpinner />}>
            <ZoneDetails />
          </Suspense>
        ),
      },
    ],
  },
]);

const container = document.querySelector('#root');
if (container) {
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <I18nextProvider i18n={i18n}>
        <HelmetProvider>
          <QueryClientProvider client={queryClient}>
            <RouterProvider router={router} />
          </QueryClientProvider>
        </HelmetProvider>
      </I18nextProvider>
    </StrictMode>
  );
}
