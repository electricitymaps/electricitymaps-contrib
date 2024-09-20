// Init CSS
import 'react-spring-bottom-sheet/dist/style.css';
import 'maplibre-gl/dist/maplibre-gl.css';
import './index.css';

import { Capacitor } from '@capacitor/core';
import * as Sentry from '@sentry/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from 'App';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { HelmetProvider } from 'react-helmet-async';
import { I18nextProvider } from 'react-i18next';
import { BrowserRouter } from 'react-router-dom';
import i18n from 'translation/i18n';
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

const container = document.querySelector('#root');
if (container) {
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <I18nextProvider i18n={i18n}>
        <HelmetProvider>
          <QueryClientProvider client={queryClient}>
            <BrowserRouter>
              <App />
            </BrowserRouter>
          </QueryClientProvider>
        </HelmetProvider>
      </I18nextProvider>
    </StrictMode>
  );
}
