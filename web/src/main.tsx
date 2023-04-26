import { StrictMode } from 'react';
import * as Sentry from '@sentry/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from 'App';
import { REFETCH_INTERVAL_FIVE_MINUTES } from 'api/helpers';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { createConsoleGreeting } from 'utils/createConsoleGreeting';
import enableErrorsInOverlay from 'utils/errorOverlay';
//import { registerSW } from 'virtual:pwa-register';

const isProduction = import.meta.env.PROD;

// Init CSS
import 'react-spring-bottom-sheet/dist/style.css';
import './index.css';

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

// Temporarily disabled to ensure we can more easily rollback
// Also removes existing service workers to ensure they don't interfer

if (navigator.serviceWorker) {
  // eslint-disable-next-line unicorn/prefer-top-level-await
  navigator.serviceWorker.getRegistrations().then(function (registrations) {
    for (const registration of registrations) {
      registration.unregister();
    }
  });
}
// registerSW();
createConsoleGreeting();

if (import.meta.env.DEV) {
  enableErrorsInOverlay();
}

const MAX_RETRIES = 1;
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: MAX_RETRIES,
      refetchInterval: REFETCH_INTERVAL_FIVE_MINUTES,
    },
  },
});

const container = document.querySelector('#root');
if (container) {
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </StrictMode>
  );
}
