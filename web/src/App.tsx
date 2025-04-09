import { App as Cap } from '@capacitor/app';
import { Capacitor } from '@capacitor/core';
import Intercom from '@intercom/messenger-js-sdk';
import { ToastProvider } from '@radix-ui/react-toast';
import { useReducedMotion } from '@react-spring/web';
import * as Sentry from '@sentry/react';
import useGetState from 'api/getState';
import { AppStoreBanner } from 'components/AppStoreBanner';
import GtmPageTracker from 'components/GtmPageTracker';
import LoadingOverlay from 'components/LoadingOverlay';
import { OnboardingModal } from 'components/modals/OnboardingModal';
import { AppSidebar, SIDEBAR_WIDTH } from 'features/app-sidebar/AppSidebar';
import ErrorComponent from 'features/error-boundary/ErrorBoundary';
import { useFeatureFlag } from 'features/feature-flags/api';
import { mapMovingAtom } from 'features/map/mapAtoms';
import UpdatePrompt from 'features/service-worker/UpdatePrompt';
import DateRedirectToast from 'features/time/DateRedirectToast';
import { useDarkMode } from 'hooks/theme';
import { useGetCanonicalUrl } from 'hooks/useGetCanonicalUrl';
import { useSetAtom } from 'jotai';
import {
  lazy,
  ReactElement,
  Suspense,
  useCallback,
  useEffect,
  useLayoutEffect,
} from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';
import { metaTitleSuffix, Mode } from 'utils/constants';
import { useNavigateWithParameters } from 'utils/helpers';
import { productionConsumptionAtom } from 'utils/state/atoms';

const MapWrapper = lazy(async () => import('features/map/MapWrapper'));
const LeftPanel = lazy(async () => import('features/panels/LeftPanel'));
const MapOverlays = lazy(() => import('components/MapOverlays'));

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
  const isIntercomEnabled = useFeatureFlag('intercom-messenger');
  const location = useLocation();
  const navigate = useNavigateWithParameters();
  const setIsMapMoving = useSetAtom(mapMovingAtom);

  useEffect(() => {
    if (isIntercomEnabled) {
      Intercom({
        app_id: 'trqbz4yj',
      });
    }
  }, [isIntercomEnabled]);

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
        if (window.location.pathname === '/map/72h/hourly') {
          Cap.exitApp();
        } else {
          window.history.back();
        }
      });
    }
  }, []);

  // Close zone panel and focus search
  const navigateToSearchAndFocus = useCallback(() => {
    if (location.pathname.startsWith('/zone')) {
      // Navigate to map if we're currently in a zone
      setIsMapMoving(false);
      navigate({
        to: '/map',
      });

      // Need to wait for navigation to complete before focusing the search input
      setTimeout(() => {
        const searchInput = document.querySelector(
          'input[data-testid="zone-search-bar"]'
        );
        if (searchInput instanceof HTMLElement) {
          searchInput.focus();
        }
      }, 100);
    } else {
      // Just focus the search input if we're already on the map
      const searchInput = document.querySelector('input[data-testid="zone-search-bar"]');
      if (searchInput instanceof HTMLElement) {
        searchInput.focus();
      }
    }
  }, [location.pathname, navigate, setIsMapMoving]);

  // Handle global keyboard shortcut for search
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check if the key pressed is '/' and not inside an input field or textarea
      if (
        event.key === '/' &&
        !['INPUT', 'TEXTAREA'].includes((event.target as HTMLElement).tagName)
      ) {
        event.preventDefault();
        navigateToSearchAndFocus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [navigateToSearchAndFocus]);

  return (
    <Suspense fallback={<div />}>
      <GtmPageTracker />

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
      <div
        className="flex h-full flex-row"
        style={{ '--sidebar-width': SIDEBAR_WIDTH } as React.CSSProperties}
      >
        <AppSidebar />
        <main className="fixed flex h-full w-full flex-col md:ml-[--sidebar-width] md:w-[calc(100%-var(--sidebar-width))]">
          <AppStoreBanner />
          <ToastProvider duration={20_000}>
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
                  <LeftPanel />
                </Suspense>
                <Suspense>
                  <MapWrapper />
                </Suspense>
                <Suspense>
                  <MapOverlays />
                </Suspense>
              </Sentry.ErrorBoundary>
            </div>
          </ToastProvider>
        </main>
      </div>
    </Suspense>
  );
}
