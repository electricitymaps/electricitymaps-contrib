import { Capacitor } from '@capacitor/core';
import { Share as CapShare } from '@capacitor/share';
import { Button, ButtonProps } from 'components/Button';
import { MemoizedShareIcon } from 'components/ShareIcon';
import { Toast, useToastReference } from 'components/Toast';
import { isIos, isMobile } from 'features/weather-layers/wind-layer/util';
import { useShare } from 'hooks/useShare';
import { Link } from 'lucide-react';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { twMerge } from 'tailwind-merge';
import { ShareType, trackShare } from 'utils/analytics';
import { baseUrl, DEFAULT_ICON_SIZE, DEFAULT_TOAST_DURATION } from 'utils/constants';

interface ShareButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
  shareUrl?: string;
  showIosIcon?: boolean;
  hasMobileUserAgent?: boolean;
}

const trackShareClick = trackShare(ShareType.SHARE);
const trackShareCompletion = trackShare(ShareType.COMPLETED_SHARE);

export function ShareButton({
  iconSize = DEFAULT_ICON_SIZE,
  shareUrl = baseUrl,
  showIosIcon = isIos(),
  hasMobileUserAgent = isMobile(),
  ...restProps
}: ShareButtonProps) {
  const { t } = useTranslation();
  const reference = useToastReference();
  const [toastMessage, setToastMessage] = useState('');
  const { copyToClipboard, share } = useShare();

  const onClick = useCallback(async () => {
    const toastMessageCallback = (message: string) => {
      setToastMessage(message);
      reference.current?.publish();
    };

    if (hasMobileUserAgent && (await CapShare.canShare())) {
      share(
        {
          title: 'Electricity Maps',
          text: 'Check this out!',
          url: shareUrl,
        },
        toastMessageCallback
      ).then((shareCompleted) => {
        if (shareCompleted) {
          trackShareCompletion();
        }
      });
    } else {
      copyToClipboard(shareUrl, toastMessageCallback);
    }
    trackShareClick();
  }, [reference, hasMobileUserAgent, copyToClipboard, share, shareUrl]);

  let shareIcon = <Link data-testid="linkIcon" size={iconSize} />;
  if (hasMobileUserAgent || Capacitor.isNativePlatform()) {
    shareIcon = <MemoizedShareIcon showIosIcon={showIosIcon} />;
  }

  return (
    <>
      <Button
        dataTestId="share-btn"
        size="md"
        backgroundClasses="bg-brand-green"
        foregroundClasses={twMerge(
          'text-white dark:text-white focus-visible:outline-black',
          showIosIcon ? '' : '-translate-x-px'
        )}
        onClick={onClick}
        icon={shareIcon}
        {...restProps}
      />
      <Toast
        ref={reference}
        description={toastMessage}
        isCloseable={true}
        toastCloseText={t('misc.dismiss')}
        duration={DEFAULT_TOAST_DURATION}
      />
    </>
  );
}
