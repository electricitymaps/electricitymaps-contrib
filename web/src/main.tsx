// Init CSS
import 'maplibre-gl/dist/maplibre-gl.css';
import 'react-spring-bottom-sheet/dist/style.css';
import './index.css';

import { Capacitor } from '@capacitor/core';
import * as Sentry from '@sentry/react';
import { captureException } from '@sentry/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TIME_RANGE_TO_TIME_AVERAGE } from 'api/helpers';
import App from 'App';
import GlassContainer from 'components/GlassContainer';
import LoadingSpinner from 'components/LoadingSpinner';
import PostHogPageView from 'components/PageView';
import { zoneExists } from 'features/panels/zone/util';
import { PostHogProvider } from 'posthog-js/react';
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
    beforeSend(event) {
      // Ignore all plausible-related errors
      if (JSON.stringify(event).toLowerCase().includes('plausible')) {
        return null;
      }
      return event;
    },
  });
}

const options = {
  api_host: 'https://eu.i.posthog.com',
  ui_host: 'https://eu.i.posthog.com',
  capture_pageview: false,
};

window.addEventListener('vite:preloadError', async (event: VitePreloadErrorEvent) => {
  event.preventDefault();

  try {
    if ('serviceWorker' in navigator) {
      const registrations = await navigator.serviceWorker.getRegistrations();
      await Promise.all(registrations.map((r) => r.unregister()));
    }

    if ('caches' in window) {
      const keys = await caches.keys();
      await Promise.all(keys.map((key) => caches.delete(key)));
    }
  } catch (cleanupError) {
    captureException(cleanupError, {
      tags: {
        type: 'preload_error_cleanup',
        hasCaches: 'caches' in window,
        hasServiceWorker: 'serviceWorker' in navigator,
      },
      extra: {
        url: window.location.href,
        timestamp: new Date().toISOString(),
        originalError: event.payload.message,
      },
    });
  }

  window.location.reload();
});

const SearchPanel = lazy(() => import('features/panels/search-panel/SearchPanel'));
const ZoneDetails = lazy(() => import('features/panels/zone/ZoneDetails'));

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

function TimeRangeAndResolutionGuardWrapper({ children }: { children: JSX.Element }) {
  const [searchParameters] = useSearchParams();
  const { urlTimeRange } = useParams<RouteParameters>();
  const location = useLocation();

  if (!urlTimeRange) {
    return (
      <Navigate
        to={`${location.pathname}/72h/hourly?${searchParameters}${location.hash}`}
        replace
      />
    );
  }
  let sanitizedTimeRange = urlTimeRange.toLowerCase();

  if (sanitizedTimeRange === '24h') {
    sanitizedTimeRange = TimeRange.H72;
  }

  if (sanitizedTimeRange === '30d') {
    sanitizedTimeRange = TimeRange.M3;
  }

  if (
    !Object.values(TimeRange).includes(sanitizedTimeRange as TimeRange) &&
    String(sanitizedTimeRange) != 'all'
  ) {
    return (
      <Navigate
        to={`${location.pathname}/72h/hourly?${searchParameters}${location.hash}`}
        replace
      />
    );
  }

  if (urlTimeRange !== sanitizedTimeRange) {
    return (
      <Navigate
        to={`${location.pathname.replace(urlTimeRange, sanitizedTimeRange)}/${
          TIME_RANGE_TO_TIME_AVERAGE[sanitizedTimeRange as TimeRange]
        }?${searchParameters}${location.hash}`}
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
    return <Navigate to={`/map/72h/hourly?${searchParameters}`} replace />;
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
    return <Navigate to={`/map/72h/hourly?${searchParameters}`} replace />;
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
        element: <Navigate to="/map/72h/hourly" replace />,
      },
      {
        path: '/zone',
        element: <Navigate to="/map/72h/hourly" replace />,
      },
      {
        path: '/map/:urlTimeRange?/:resolution?/:urlDatetime?',
        element: (
          <TimeRangeAndResolutionGuardWrapper>
            <>
              <SearchPanel />
              <PostHogPageView />
            </>
          </TimeRangeAndResolutionGuardWrapper>
        ),
      },
      {
        path: '/zone/:zoneId/:urlTimeRange?/:resolution?/:urlDatetime?',
        element: (
          <ValidZoneIdGuardWrapper>
            <TimeRangeAndResolutionGuardWrapper>
              <Suspense
                fallback={
                  <GlassContainer className="pointer-events-auto h-full sm:inset-3 sm:bottom-36 sm:h-auto">
                    <LoadingSpinner />
                  </GlassContainer>
                }
              >
                <ZoneDetails />
                <PostHogPageView />
              </Suspense>
            </TimeRangeAndResolutionGuardWrapper>
          </ValidZoneIdGuardWrapper>
        ),
      },
      {
        path: '*',
        element: (
          <Suspense fallback={<LoadingSpinner />}>
            <ZoneDetails />
            <PostHogPageView />
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
        <PostHogProvider
          apiKey={import.meta.env.API_PORTAL_POSTHOG_KEY}
          options={options}
        >
          <HelmetProvider>
            <QueryClientProvider client={queryClient}>
              <RouterProvider router={router} />
            </QueryClientProvider>
          </HelmetProvider>
        </PostHogProvider>
      </I18nextProvider>
    </StrictMode>
  );
}
