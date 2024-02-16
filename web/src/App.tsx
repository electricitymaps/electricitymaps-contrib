import { App as Cap } from '@capacitor/app';
import { Capacitor } from '@capacitor/core';
import { ToastProvider } from '@radix-ui/react-toast';
import * as Sentry from '@sentry/react';
import { useGetAppVersion } from 'api/getAppVersion';
import useGetState from 'api/getState';
import LoadingOverlay from 'components/LoadingOverlay';
import { OnboardingModal } from 'components/modals/OnboardingModal';
import Toast from 'components/Toast';
import ErrorComponent from 'features/error-boundary/ErrorBoundary';
import FeatureFlagsManager from 'features/feature-flags/FeatureFlagsManager';
import Header from 'features/header/Header';
import TimeControllerWrapper from 'features/time/TimeControllerWrapper';
import { useDarkMode } from 'hooks/theme';
import { lazy, ReactElement, Suspense, useEffect, useLayoutEffect } from 'react';
import i18n from 'translation/i18n';
import trackEvent from 'utils/analytics';

const MapWrapper = lazy(async () => import('features/map/MapWrapper'));
const LeftPanel = lazy(async () => import('features/panels/LeftPanel'));
const LegendContainer = lazy(() => import('components/legend/LegendContainer'));
const FAQModal = lazy(() => import('features/modals/FAQModal'));
const InfoModal = lazy(() => import('features/modals/InfoModal'));
const SettingsModal = lazy(() => import('features/modals/SettingsModal'));

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
  // Triggering the useGetState hook here ensures that the app starts loading data as soon as possible
  // instead of waiting for the map to be lazy loaded.
  const _ = useGetState();
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
          <Suspense>
            <Header />
          </Suspense>
          <div className="relative flex flex-auto items-stretch">
            <Sentry.ErrorBoundary fallback={ErrorComponent} showDialog>
              {isSuccess && isNewVersionAvailable && (
                <Toast
                  title={i18n.t('misc.newversion')}
                  toastAction={handleReload}
                  isCloseable={true}
                  toastActionText={i18n.t('misc.reload')}
                />
              )}
              <Suspense>
                <LoadingOverlay />
              </Suspense>
              <Suspense>
                <OnboardingModal />
              </Suspense>
              <Suspense>
                <FAQModal />
                <InfoModal />
                <SettingsModal />
              </Suspense>
              <Suspense>
                <LeftPanel />
              </Suspense>
              <Suspense>
                <MapWrapper />
              </Suspense>
              <Suspense>
                <TimeControllerWrapper />
              </Suspense>
              <Suspense>
                <FeatureFlagsManager />
              </Suspense>
              <Suspense>
                <LegendContainer />
              </Suspense>
            </Sentry.ErrorBoundary>
          </div>
        </ToastProvider>
      </main>
    </Suspense>
  );
}
