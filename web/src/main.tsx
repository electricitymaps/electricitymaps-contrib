import App from 'App';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { registerSW } from 'virtual:pwa-register';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import './index.css';

registerSW();

const MAX_RETRIES = 1;
const REFETCH_INTERVAL_MS = 1000 * 60 * 5; // 5 minutes
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
        <App />
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </StrictMode>
  );
}
