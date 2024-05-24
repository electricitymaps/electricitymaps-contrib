/* eslint-disable no-prototype-builtins */
/* eslint-disable no-restricted-syntax */
import { App as Cap } from '@capacitor/app';
import { Capacitor } from '@capacitor/core';
import { ToastProvider } from '@radix-ui/react-toast';
import * as Sentry from '@sentry/react';
import { useGetAppVersion } from 'api/getAppVersion';
import useGetState from 'api/getState';
import LoadingOverlay from 'components/LoadingOverlay';
import { OnboardingModal } from 'components/modals/OnboardingModal';
import Toast from 'components/Toast';
import { formatInTimeZone } from 'date-fns-tz';
import ErrorComponent from 'features/error-boundary/ErrorBoundary';
import FeatureFlagsManager from 'features/feature-flags/FeatureFlagsManager';
import Header from 'features/header/Header';
import { useDarkMode } from 'hooks/theme';
import { useSetAtom } from 'jotai';
import { lazy, ReactElement, Suspense, useEffect, useLayoutEffect } from 'react';
import i18n from 'translation/i18n';
import { StateExchangeData, StateZoneData, ZoneKey } from 'types';
import trackEvent from 'utils/analytics';
import { emapleDatetimeAtom, emapleZoneAtom } from 'utils/state/atoms';
import { ZoneGuessInput } from 'ZoneGuessInput';

const MapWrapper = lazy(async () => import('features/map/MapWrapper'));
const LeftPanel = lazy(async () => import('features/panels/LeftPanel'));
const LegendContainer = lazy(() => import('components/legend/LegendContainer'));
const FAQModal = lazy(() => import('features/modals/FAQModal'));
const InfoModal = lazy(() => import('features/modals/InfoModal'));
const SettingsModal = lazy(() => import('features/modals/SettingsModal'));
const TimeControllerWrapper = lazy(() => import('features/time/TimeControllerWrapper'));

const isProduction = import.meta.env.PROD;

if (isProduction) {
  trackEvent('App Loaded', {
    isNative: Capacitor.isNativePlatform(),
    platform: Capacitor.getPlatform(),
  });
}

function getTimeZone(lat: number, lng: number): string {
  // TODO: Figure out a way to do that?
  // const TIMEZONE_API_KEY = '1CC11PQMT0TE';
  // const options = {
  //   method: 'GET',
  //   // headers: {
  //   //   'Content-Type': 'application/json',
  //   // },
  //   mode: 'no-cors',
  // };
  // const response = await fetch(`https://api.timezonedb.com/v2.1/get-time-zone?key=${TIMEZONE_API_KEY}&format=json&by=position&lat=${lat}&lng=${lng}`, options);
  // const data = await response.json();
  return 'UTC';
}

function getCallerTimeZone(latitude: number, longitude: number): string {
  try {
    const timeZone = getTimeZone(latitude, longitude);
    return timeZone;
  } catch (error) {
    console.error('Error getting timezone:', error);
    throw error;
  }
}

function getCurrentDateInTimeZone(latitude: number, longitude: number): number {
  try {
    const timeZone = getCallerTimeZone(latitude, longitude);
    const currentDate = new Date();
    const formattedDate = formatInTimeZone(currentDate, timeZone, 'yyyyMMdd');
    return Number.parseInt(formattedDate, 10);
  } catch (error) {
    console.error('Error getting current date in timezone:', error);
    throw error;
  }
}

const randomInt = (seed: number, min: number, max: number) => {
  const random = () => {
    const x = Math.sin(seed++) * 10_000;
    return x - Math.floor(x);
  };
  return Math.floor(random() * (max - min + 1)) + min;
};

interface ZoneState {
  e: {
    [key: ZoneKey]: StateExchangeData;
  };
  z: {
    [key: ZoneKey]: StateZoneData;
  };
}

function filterZonesByCi(state: ZoneState) {
  const filteredZones: { [key: ZoneKey]: StateZoneData } = {};

  for (const zoneKey in state.z) {
    if (state.z.hasOwnProperty(zoneKey)) {
      const zone = state.z[zoneKey];
      if (zone.c && zone.c.ci !== null) {
        filteredZones[zoneKey] = zone;
      }
    }
  }

  return filteredZones;
}

function pick_one_state_for_date(hourly_data: any): [string, string] {
  console.log('hourly_data', hourly_data);
  const [lat, lng] = hourly_data.callerLocation;
  const localDate = getCurrentDateInTimeZone(lat, lng);
  // Seed for random selection is the localDate

  const datetimeIndex = randomInt(
    localDate,
    0,
    Object.keys(hourly_data.data.datetimes).length - 1
  );
  const state =
    hourly_data.data.datetimes[Object.keys(hourly_data.data.datetimes)[datetimeIndex]];
  console.log('state', state);

  const validZones = filterZonesByCi(state);
  const zoneKeyIndex = randomInt(localDate, 0, Object.keys(validZones).length - 1);
  const zoneKey = Object.keys(validZones)[zoneKeyIndex];

  console.log('validZones', validZones);
  console.log('zoneKey', zoneKey);

  return [Object.keys(hourly_data.data.datetimes)[datetimeIndex], zoneKey];
}

const handleReload = () => {
  window.location.reload();
};
export default function App(): ReactElement {
  // Triggering the useGetState hook here ensures that the app starts loading data as soon as possible
  // instead of waiting for the map to be lazy loaded.
  const { data: hourly_data, isSuccess: successfullyLoaded } = useGetState();
  const setEmapsleZone = useSetAtom(emapleZoneAtom);
  const setEmapsleDatetime = useSetAtom(emapleDatetimeAtom);
  const [datetime, zoneKey] = successfullyLoaded
    ? pick_one_state_for_date(hourly_data)
    : [null, null];
  console.log('datetime', datetime);
  console.log('zoneKey', zoneKey);
  if (zoneKey) {
    setEmapsleZone(zoneKey);
  }
  if (datetime) {
    setEmapsleDatetime(datetime);
  }
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
              <div className="invisible fixed bottom-[40%] right-[25%] z-20 flex w-[550px] flex-col rounded bg-white/90 px-1 py-2 shadow-xl backdrop-blur-sm sm:visible dark:bg-gray-800">
                <ZoneGuessInput />
              </div>
            </Sentry.ErrorBoundary>
          </div>
        </ToastProvider>
      </main>
    </Suspense>
  );
}
