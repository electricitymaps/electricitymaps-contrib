import { Capacitor } from '@capacitor/core';
import { Share as CapShare } from '@capacitor/share';
import { Button, ButtonProps } from 'components/Button';
import { ShareIcon } from 'components/ShareIcon';
import { Toast, useToastReference } from 'components/Toast';
import { isIos, isMobile } from 'features/weather-layers/wind-layer/util';
import { useShare } from 'hooks/useShare';
import { Link } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { twMerge } from 'tailwind-merge';
import { ShareType, trackShare } from 'utils/analytics';
import { baseUrl, DEFAULT_ICON_SIZE } from 'utils/constants';

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
  shareUrl = baseUrl,
  showIosIcon = isIos(),
  hasMobileUserAgent = isMobile(),
  ...restProps
}: ShareButtonProps) {
  const { t } = useTranslation();
  const reference = useToastReference();
  const [toastMessage, setToastMessage] = useState('');
  const { copyToClipboard, share } = useShare();

  const shareData = {
    title: 'Electricity Maps',
    text: 'Check this out!',
    url: shareUrl,
  };

  // TODO: callbacks -> individually useCallback'd or useMemo'd as a group
  const toastMessageCallback = (message: string) => {
    setToastMessage(message);
    reference.current?.publish();
  };
  const copyShareUrl = () => copyToClipboard(shareUrl, toastMessageCallback);
  const onShare = () => share(shareData, toastMessageCallback);

  const onClick = async () => {
    if (hasMobileUserAgent && (await CapShare.canShare())) {
      onShare();
    } else {
      copyShareUrl();
    }
    trackShareClick();
  };

  let shareIcon = <Link data-test-id="linkIcon" size={iconSize} />;
  if (hasMobileUserAgent || Capacitor.isNativePlatform()) {
    shareIcon = <ShareIcon />;
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
