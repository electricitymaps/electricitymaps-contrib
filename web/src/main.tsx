// Init CSS
import 'react-spring-bottom-sheet/dist/style.css';
import 'maplibre-gl/dist/maplibre-gl.css';
import './index.css';

import * as Sentry from '@sentry/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from 'App';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { I18nextProvider } from 'react-i18next';
import { BrowserRouter } from 'react-router-dom';
import i18n from 'translation/i18n';
import { createConsoleGreeting } from 'utils/createConsoleGreeting';
import enableErrorsInOverlay from 'utils/errorOverlay';
import { refetchDataOnHourChange } from 'utils/refetching';

const isProduction = import.meta.env.PROD;

if (isProduction) {
  Sentry.init({
    dsn: 'https://bbe4fb6e5b3c4b96a1df95145a91e744@o192958.ingest.sentry.io/4504366922989568', //We should create a capacitor project in Sentry for the mobile app
    tracesSampleRate: 0, // Disables tracing completely as we don't use it and sends a lot of data
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
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </QueryClientProvider>
      </I18nextProvider>
    </StrictMode>
  );
}
