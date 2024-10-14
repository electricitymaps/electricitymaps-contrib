import { Capacitor } from '@capacitor/core';
import { Share as CapShare } from '@capacitor/share';
import { Button, ButtonProps } from 'components/Button';
import { Toast, useToastReference } from 'components/Toast';
import { isIos, isMobile } from 'features/weather-layers/wind-layer/util';
import { Link, Share, Share2 } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { twMerge } from 'tailwind-merge';
import { ShareType, trackShare } from 'utils/analytics';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

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
const DURATION = 3 * 1000;

export function ShareButton({
  iconSize = DEFAULT_ICON_SIZE,
  shareUrl,
  showIosIcon = isIos(),
  hasMobileUserAgent = isMobile(),
  ...restProps
}: ShareButtonProps) {
  const { t } = useTranslation();
  const reference = useToastReference();
  const [toastMessage, setToastMessage] = useState('');

  const url = shareUrl ?? window.location?.href;

  const shareData = {
    title: 'Electricity Maps',
    text: 'Check this out!',
    url,
  };

  const share = async () => {
    try {
      await CapShare.share(shareData);
    } catch (error) {
      if (error instanceof Error && !/AbortError|canceled/.test(error.toString())) {
        console.error(error);
        setToastMessage(t('share-button.share-error'));
        reference.current?.publish();
      }
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setToastMessage(t('share-button.clipboard'));
    } catch (error) {
      console.error(error);
      setToastMessage(t('share-button.clipboard-error'));
    } finally {
      reference.current?.publish();
    }
  };

  const onClick = async () => {
    if (hasMobileUserAgent && (await CapShare.canShare())) {
      share();
    } else {
      copyToClipboard();
    }
    trackShareClick();
  };

  let shareIcon = <Link data-test-id="linkIcon" size={iconSize} />;
  if (hasMobileUserAgent || Capacitor.isNativePlatform()) {
    shareIcon = showIosIcon ? (
      <Share data-test-id="iosShareIcon" size={iconSize} />
    ) : (
      <Share2 data-test-id="defaultShareIcon" size={iconSize} />
    );
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
        duration={DURATION}
      />
    </>
  );
}
