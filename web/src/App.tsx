import { ToastProvider } from '@radix-ui/react-toast';
import { useGetAppVersion } from 'api/getAppVersion';
import LoadingOverlay from 'components/LoadingOverlay';
import { OnboardingModal } from 'components/modals/OnboardingModal';
import Toast from 'components/Toast';
import ErrorBoundary from 'features/error-boundary/ErrorBoundary';
import Header from 'features/header/Header';
import MapControls from 'features/map-controls/MapControls';
import TimeControllerWrapper from 'features/time/TimeControllerWrapper';
import { lazy, ReactElement, Suspense } from 'react';

const isProduction = import.meta.env.PROD;

const Map = lazy(async () => import('features/map/Map'));
const LeftPanel = lazy(async () => import('features/panels/LeftPanel'));
const handleReload = () => {
  window.location.reload();
};
export default function App(): ReactElement {
  //@ts-ignore Use global variable from Vite
  const currentAppVersion = APP_VERSION;
  const { data, isSuccess } = useGetAppVersion();
  const isNewVersionAvailable =
    data?.version && currentAppVersion && isProduction
      ? data.version !== currentAppVersion
      : false;

  return (
    <Suspense fallback={<div />}>
      <main className="fixed flex h-screen w-screen flex-col">
        <ToastProvider duration={20_000}>
          <Header />
          <div className="relative flex flex-auto items-stretch">
            <ErrorBoundary>
              {isSuccess && isNewVersionAvailable && (
                <Toast
                  title="A new app version is available"
                  toastAction={handleReload}
                  isCloseable={true}
                  toastActionText="Reload"
                />
              )}
              <LoadingOverlay />
              <OnboardingModal />
              <LeftPanel />
              <Map />
              <TimeControllerWrapper />
              <MapControls />
            </ErrorBoundary>
          </div>
        </ToastProvider>
      </main>
    </Suspense>
  );
}
