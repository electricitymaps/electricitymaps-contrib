import { Button, ButtonProps } from 'components/Button';
import { Toast, useToastReference } from 'components/Toast';
import { isiOS, isMobile } from 'features/weather-layers/wind-layer/util';
import { t } from 'i18next';
import { Share, Share2 } from 'lucide-react';
import { useState } from 'react';
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
  showiOSIcon?: boolean;
}
const trackShareClick = trackShare(ShareType.SHARE);
const DURATION = 3 * 1000;

export function ShareButton({
  iconSize = DEFAULT_ICON_SIZE,
  shareUrl,
  showiOSIcon = isiOS(),
  ...restProps
}: ShareButtonProps) {
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
      await navigator.share(shareData);
    } catch (error) {
      console.error(error);
      setToastMessage('Error sharing URL');
      reference.current?.publish();
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setToastMessage('URL copied to clipboard!');
    } catch (error) {
      console.error(error);
      setToastMessage('Error copying URL to clipboard');
    } finally {
      reference.current?.publish();
    }
  };

  const onClick = () => {
    if (isMobile() && navigator.canShare()) {
      share();
    } else {
      copyToClipboard();
    }
    trackShareClick();
  };

  return (
    <>
      <Button
        dataTestId="share-btn"
        size="md"
        backgroundClasses="bg-brand-green"
        foregroundClasses={twMerge(
          'text-white dark:text-white focus-visible:outline-black',
          showiOSIcon ? '' : '-translate-x-px'
        )}
        onClick={onClick}
        icon={
          showiOSIcon ? (
            <Share data-test-id="iosShareIcon" size={iconSize} />
          ) : (
            <Share2 data-test-id="defaultShareIcon" size={iconSize} />
          )
        }
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
