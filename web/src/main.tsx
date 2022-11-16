import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { REFETCH_INTERVAL_MS } from 'api/helpers';
import App from 'App';
import { useAtomsDevtools } from 'jotai/devtools';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { createConsoleGreeting } from 'utils/createConsoleGreeting';
import enableErrorsInOverlay from 'utils/errorOverlay';
import { registerSW } from 'virtual:pwa-register';
import './index.css';

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
      refetchInterval: REFETCH_INTERVAL_MS,
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
        <ReactQueryDevtools position="bottom-right" initialIsOpen={false} />
      </QueryClientProvider>
    </StrictMode>
  );
}
