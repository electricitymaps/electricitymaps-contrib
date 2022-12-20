import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { REFETCH_INTERVAL_FIVE_MINUTES } from 'api/helpers';
import App from 'App';
import { useAtomsDevtools } from 'jotai/devtools';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { createConsoleGreeting } from 'utils/createConsoleGreeting';
import enableErrorsInOverlay from 'utils/errorOverlay';
import { registerSW } from 'virtual:pwa-register';

// Init CSS
import 'react-spring-bottom-sheet/dist/style.css';
import './index.css';

// Init polyfills
import { StrictMode } from 'react';
import 'utils/polyfills';

/**
 * DevTools for Jotai which makes atoms appear in Redux Dev Tools.
 * Only enabled on import.meta.env.DEV
 */
const AtomsDevtools = ({ children }: { children: JSX.Element }) => {
  useAtomsDevtools('demo');
  return children;
};

registerSW();
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
          <AtomsDevtools>
            <App />
          </AtomsDevtools>
        </BrowserRouter>
        <ReactQueryDevtools position="top-right" initialIsOpen={false} />
      </QueryClientProvider>
    </StrictMode>
  );
}
