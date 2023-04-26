import { ToastProvider } from '@radix-ui/react-toast';
import * as Sentry from '@sentry/react';
import { useGetAppVersion } from 'api/getAppVersion';
import LoadingOverlay from 'components/LoadingOverlay';
import Toast from 'components/Toast';
import LegendContainer from 'components/legend/LegendContainer';
import { OnboardingModal } from 'components/modals/OnboardingModal';
import ErrorComponent from 'features/error-boundary/ErrorBoundary';
import Header from 'features/header/Header';
import FAQModal from 'features/modals/FAQModal';
import InfoModal from 'features/modals/InfoModal';
import SettingsModal from 'features/modals/SettingsModal';
import TimeControllerWrapper from 'features/time/TimeControllerWrapper';
import { ReactElement, Suspense, lazy, useEffect, useLayoutEffect } from 'react';
import { Capacitor } from '@capacitor/core';
import { App as Cap } from '@capacitor/app';
import trackEvent from 'utils/analytics';
import { useDarkMode } from 'hooks/theme';

const MapWrapper = lazy(async () => import('features/map/MapWrapper'));
const LeftPanel = lazy(async () => import('features/panels/LeftPanel'));

const isProduction = import.meta.env.PROD;

if (isProduction) {
  trackEvent('App Loaded', {
    isNative: Capacitor.isNativePlatform(),
    platform: Capacitor.getPlatform(),
  });
}

const handleReload = () => {
  window.location.reload();
};
export default function App(): ReactElement {
  const shouldUseDarkMode = useDarkMode();
  const currentAppVersion = APP_VERSION;
  const { data, isSuccess } = useGetAppVersion();
  const latestAppVersion = data?.version || '0';
  const isNewVersionAvailable = isProduction && latestAppVersion > currentAppVersion;

  // Update classes on theme change
  useLayoutEffect(() => {
    if (shouldUseDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [shouldUseDarkMode]);

  // Handle back button on Android
  useEffect(() => {
    if (Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'android') {
      Cap.addListener('backButton', () => {
        if (window.location.pathname === '/map') {
          Cap.exitApp();
        } else {
          window.history.back();
        }
      });
    }
  }, []);

  return (
    <Suspense fallback={<div />}>
      <main className="fixed flex h-screen w-screen flex-col">
        <ToastProvider duration={20_000}>
          <Header />
          <div className="relative flex flex-auto items-stretch">
            <Sentry.ErrorBoundary fallback={ErrorComponent} showDialog>
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
              <FAQModal />
              <InfoModal />
              <SettingsModal />
              <LeftPanel />
              <MapWrapper />
              <TimeControllerWrapper />
              <LegendContainer />
            </Sentry.ErrorBoundary>
          </div>
        </ToastProvider>
      </main>
    </Suspense>
  );
}
