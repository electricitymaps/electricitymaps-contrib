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
import { zoneExists } from 'features/panels/zone/util';
import UpdatePrompt from 'features/service-worker/UpdatePrompt';
import { useDarkMode } from 'hooks/theme';
import { useGetCanonicalUrl } from 'hooks/useGetCanonicalUrl';
import { useSetAtom } from 'jotai';
import { lazy, ReactElement, Suspense, useEffect, useLayoutEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import { Navigate, Route, Routes, useParams, useSearchParams } from 'react-router-dom';
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

function HandleLegacyRoutes() {
  const [searchParameters] = useSearchParams();

  const page = (searchParameters.get('page') || 'map')
    .replace('country', 'zone')
    .replace('highscore', 'ranking');
  searchParameters.delete('page');

  const zoneId = searchParameters.get('countryCode');
  searchParameters.delete('countryCode');

  return (
    <Navigate
      to={{
        pathname: zoneId ? `/zone/${zoneId}` : `/${page}`,
        search: searchParameters.toString(),
      }}
    />
  );
}

function ValidZoneIdGuardWrapper({ children }: { children: JSX.Element }) {
  const [searchParameters] = useSearchParams();
  const { zoneId } = useParams();

  if (!zoneId) {
    return <Navigate to="/" replace />;
  }
  const upperCaseZoneId = zoneId.toUpperCase();
  if (zoneId !== upperCaseZoneId) {
    return <Navigate to={`/zone/${upperCaseZoneId}?${searchParameters}`} replace />;
  }

  // Handle legacy Australia zone names
  if (upperCaseZoneId.startsWith('AUS')) {
    return (
      <Navigate to={`/zone/${zoneId.replace('AUS', 'AU')}?${searchParameters}`} replace />
    );
  }

  // Only allow valid zone ids
  // TODO: This should redirect to a 404 page specifically for zones
  if (!zoneExists(upperCaseZoneId)) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default function App(): ReactElement {
  useReducedMotion();
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

  useLayoutEffect(() => {
    document.documentElement.classList.toggle('dark', shouldUseDarkMode);
  }, [shouldUseDarkMode]);

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

  if (isProduction) {
    trackEvent(TrackEvent.APP_LOADED, {
      isNative: Capacitor.isNativePlatform(),
      platform: Capacitor.getPlatform(),
    });
  }

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
                <Suspense>
                  <Routes>
                    <Route path="/" element={<HandleLegacyRoutes />} />
                    <Route
                      path="/zone/:zoneId/:urlTimeAverage?/:urlDatetime?"
                      element={
                        <ValidZoneIdGuardWrapper>
                          <LeftPanel />
                        </ValidZoneIdGuardWrapper>
                      }
                    />
                    <Route path="*" element={<LeftPanel />} />
                  </Routes>
                </Suspense>
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
