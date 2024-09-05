import { EmapsIcon } from 'icons/emapsIcon';
import { useAtom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { X } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import trackEvent from 'utils/analytics';
import { TrackEvent } from 'utils/constants';

import { isAndroid, isIphone } from '../features/weather-layers/wind-layer/util';
import { Button } from './Button';

export const appStoreDismissedAtom = atomWithStorage('isAppBannerDismissed', false);

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

  return (
    appStoreUrl && (
      <div
        role="banner"
        aria-live="polite"
        className="sticky z-50 flex h-14 min-h-14 w-full items-center border-b border-solid border-neutral-300 bg-neutral-100 px-3"
      >
        <CloseButton onClose={closeBanner} />
        <div className="flex flex-grow gap-2">
          <div className="items-center justify-center self-center rounded-md border border-neutral-200 bg-white">
            <EmapsIcon size={40} />
          </div>
          <div className="content-center text-neutral-600">
            <h3>Electricity Maps</h3>
            <p className="text-xs">{t('app-banner.description')}</p>
          </div>
        </div>
        <Button
          size="md"
          backgroundClasses={'h-9'}
          href={appStoreUrl}
          onClick={trackCTAClick}
        >
          {t('app-banner.cta')}
        </Button>
      </div>
    )
  );
}

export const trackCTAClick = () => trackEvent(TrackEvent.APP_BANNER_CTA_CLICKED);

interface DefaultCloseButtonProps {
  onClose(): void;
}

function DefaultCloseButton({ onClose }: DefaultCloseButtonProps) {
  const { t } = useTranslation();
  return (
    <button
      aria-label={t('misc.dismiss')}
      data-testid="dismiss-btn"
      onClick={onClose}
      className="pointer-events-auto flex h-6 w-6 items-center justify-center self-center pr-2 text-neutral-400"
    >
      <X />
    </button>
  );
}

interface AppStoreBannerState {
  appStoreUrl: string | undefined;
  closeBanner(): void;
}

const useAppStoreBannerState = (): AppStoreBannerState => {
  const [appStoreIsDismissed, setAppStoreIsDismissed] = useAtom(appStoreDismissedAtom);
  const [appStoreUrl, setAppStoreUrl] = useState(getAppStoreUrl(appStoreIsDismissed));

  return {
    appStoreUrl,
    closeBanner: () => {
      setAppStoreIsDismissed(true);
      trackEvent(TrackEvent.APP_BANNER_DISMISSED);
      setAppStoreUrl(undefined);
    },
  };
};

function getAppStoreUrl(appStoreIsDismissed: boolean): AppStoreURLs | undefined {
  if (appStoreIsDismissed) {
    return undefined;
  }

  if (isAndroid()) {
    return AppStoreURLs.GOOGLE;
  }

  if (isIphone()) {
    return AppStoreURLs.APPLE;
  }
}
