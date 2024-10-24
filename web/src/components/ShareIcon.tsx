import { Capacitor } from '@capacitor/core';
import { Share, Share2 } from 'lucide-react';
import { memo } from 'react';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

export function ShareIcon({
  showIosIcon = defaultShouldShowIosIcon(),
  iconSize = DEFAULT_ICON_SIZE,
}: {
  showIosIcon?: boolean;
  iconSize?: number;
}) {
  return showIosIcon ? (
    <Share data-test-id="iosShareIcon" size={iconSize} />
  ) : (
    <Share2 data-test-id="defaultShareIcon" size={iconSize} />
  );
}

export const defaultShouldShowIosIcon = () =>
  /Mac|iPad|iPhone|iPod/.test(navigator.userAgent) || Capacitor.getPlatform() === 'ios';

export const MemoizedShareIcon = memo(ShareIcon);
