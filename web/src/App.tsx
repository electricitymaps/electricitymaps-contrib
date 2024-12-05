import { App as Cap } from '@capacitor/app';
import { Capacitor } from '@capacitor/core';
import { ToastProvider } from '@radix-ui/react-toast';
import { useReducedMotion } from '@react-spring/web';
import * as Sentry from '@sentry/react';
import useGetState from 'api/getState';
import { AppStoreBanner } from 'components/AppStoreBanner';
import LoadingOverlay from 'components/LoadingOverlay';
import { OnboardingModal } from 'components/modals/OnboardingModal';
import ErrorComponent from 'features/error-boundary/ErrorBoundary';
import { useFeatureFlag } from 'features/feature-flags/api';
import Header from 'features/header/Header';
import UpdatePrompt from 'features/service-worker/UpdatePrompt';
import DateRedirectToast from 'features/time/DateRedirectToast';
import { useDarkMode } from 'hooks/theme';
import { useGetCanonicalUrl } from 'hooks/useGetCanonicalUrl';
import { useSetAtom } from 'jotai';
import { lazy, ReactElement, Suspense, useEffect, useLayoutEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import trackEvent from 'utils/analytics';
import { metaTitleSuffix, Mode, TrackEvent } from 'utils/constants';
import { productionConsumptionAtom } from 'utils/state/atoms';

const MapWrapper = lazy(async () => import('features/map/MapWrapper'));
const LeftPanel = lazy(async () => import('features/panels/LeftPanel'));
const MapOverlays = lazy(() => import('components/MapOverlays'));
const FAQModal = lazy(() => import('features/modals/FAQModal'));
const InfoModal = lazy(() => import('features/modals/InfoModal'));
const SettingsModal = lazy(() => import('features/modals/SettingsModal'));
const TimeControllerWrapper = lazy(() => import('features/time/TimeControllerWrapper'));

const isProduction = import.meta.env.PROD;

if (isProduction) {
  trackEvent(TrackEvent.APP_LOADED, {
    isNative: Capacitor.isNativePlatform(),
    platform: Capacitor.getPlatform(),
  });
}

export default function App(): ReactElement {
  // Triggering the useReducedMotion hook here ensures the global animation settings are set as soon as possible
  useReducedMotion();

  // Triggering the useGetState hook here ensures that the app starts loading data as soon as possible
  // instead of waiting for the map to be lazy loaded.
  // TODO: Replace this with prefetching once we have latest endpoints available for all state aggregates
  useGetState();
  const shouldUseDarkMode = useDarkMode();
  const { t, i18n } = useTranslation();
  const canonicalUrl = useGetCanonicalUrl();
  const setConsumptionAtom = useSetAtom(productionConsumptionAtom);
  const isConsumptionOnlyMode = useFeatureFlag('consumption-only');

  useEffect(() => {
    if (isConsumptionOnlyMode) {
      setConsumptionAtom(Mode.CONSUMPTION);
    }
  }, [isConsumptionOnlyMode, setConsumptionAtom]);

  // Update classes on theme change
  useLayoutEffect(() => {
    document.documentElement.classList.toggle('dark', shouldUseDarkMode);
  }, [shouldUseDarkMode]);

  // Handle back button on Android
  useEffect(() => {
    if (Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'android') {
      Cap.addListener('backButton', () => {
        if (window.location.pathname === '/map/24h') {
          Cap.exitApp();
        } else {
          window.history.back();
        }
      });
    }
  }, []);

  return (
    <Suspense fallback={<div />}>
      <Helmet
        htmlAttributes={{
          lang: i18n.languages[0],
          xmlns: 'http://www.w3.org/1999/xhtml',
          'xmlns:fb': 'http://ogp.me/ns/fb#',
        }}
        prioritizeSeoTags
      >
        <title>{t('misc.maintitle') + metaTitleSuffix}</title>
        <meta property="og:locale" content={i18n.languages[0]} />
        <link rel="canonical" href={canonicalUrl} />
      </Helmet>
      <main className="fixed flex h-full w-full flex-col">
        <AppStoreBanner />
        <ToastProvider duration={20_000}>
          <Suspense>
            <Header />
          </Suspense>
          <div className="relative flex flex-auto items-stretch">
            <Sentry.ErrorBoundary fallback={ErrorComponent} showDialog>
              <Suspense>
                <UpdatePrompt />
              </Suspense>
              <Suspense>
                <DateRedirectToast />
              </Suspense>
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
                <MapOverlays />
              </Suspense>
            </Sentry.ErrorBoundary>
          </div>
        </ToastProvider>
      </main>
    </Suspense>
  );
}
