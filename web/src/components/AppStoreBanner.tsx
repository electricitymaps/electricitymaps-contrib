import { useAtom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import trackEvent from 'utils/analytics';
import { TrackEvent } from 'utils/constants';

import {
  isAndroid,
  isIphone,
  isMobileWeb,
} from '../features/weather-layers/wind-layer/util';
import { Button } from './Button';
import { DefaultCloseButton, DefaultCloseButtonProps } from './DefaultCloseButton';
import { LogoIcon } from './Logo';

export const appStoreDismissedAtom = atomWithStorage(
  'isAppBannerDismissed',
  Boolean(localStorage.getItem('isAppBannerDismissed')) ?? false
);

export const trackCTAClick = () => trackEvent(TrackEvent.APP_BANNER_CTA_CLICKED);
export const trackDismissClick = () => trackEvent(TrackEvent.APP_BANNER_DISMISSED);

export enum AppStoreURLs {
  APPLE = 'https://apps.apple.com/us/app/electricity-maps/id1224594248',
  GOOGLE = 'https://play.google.com/store/apps/details?id=com.tmrow.electricitymap&hl=en',
}

export interface AppStoreBannerProps {
  CloseButton?({ onClose }: DefaultCloseButtonProps): React.ReactNode;
}

export function AppStoreBanner({
  CloseButton = DefaultCloseButton,
}: AppStoreBannerProps) {
  const { appStoreUrl, closeBanner } = useAppStoreBannerState();
  const { t } = useTranslation();

  const onCTAClick = () => closeBanner(trackCTAClick);
  const onDismissClick = () => closeBanner(trackDismissClick);

  return (
    appStoreUrl && (
      <div
        role="banner"
        aria-live="polite"
        className="sticky z-50 flex h-14 min-h-14 w-full items-center gap-2 border-b border-solid border-neutral-300 bg-neutral-100 px-3 dark:border-b dark:border-neutral-700 dark:bg-neutral-800"
      >
        <CloseButton onClose={onDismissClick} />
        <div className="flex flex-grow gap-2">
          <div className="items-center justify-center self-center rounded-md border border-neutral-200 bg-white dark:text-black">
            <LogoIcon className="size-10" />
          </div>
          <div className="content-center text-neutral-600 dark:text-neutral-300">
            <h3>Electricity Maps</h3>
            <p className="text-xs">{t('app-banner.description')}</p>
          </div>
        </div>
        <Button
          size="md"
          backgroundClasses={'h-9'}
          href={appStoreUrl}
          onClick={onCTAClick}
        >
          {t('app-banner.cta')}
        </Button>
      </div>
    )
  );
}

interface AppStoreBannerState {
  appStoreUrl: string | undefined;
  closeBanner(trackCallback?: () => void): void;
}

const useAppStoreBannerState = (): AppStoreBannerState => {
  const [appStoreIsDismissed, setAppStoreIsDismissed] = useAtom(appStoreDismissedAtom);
  const [appStoreUrl, setAppStoreUrl] = useState(getAppStoreUrl(appStoreIsDismissed));

  return {
    appStoreUrl,
    closeBanner: (trackCallback?: () => void) => {
      setAppStoreIsDismissed(true);
      trackCallback?.();
      setAppStoreUrl(undefined);
    },
  };
};

const getAppStoreUrl = (appStoreIsDismissed: boolean): AppStoreURLs | undefined => {
  if (appStoreIsDismissed || !isMobileWeb()) {
    return undefined;
  }

  if (isAndroid()) {
    return AppStoreURLs.GOOGLE;
  }

  if (isIphone()) {
    return AppStoreURLs.APPLE;
  }
};
