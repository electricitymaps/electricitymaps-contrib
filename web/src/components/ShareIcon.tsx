import { Capacitor } from '@capacitor/core';
import { Share, Share2 } from 'lucide-react';
import { memo } from 'react';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

const IOS_DEVICE_PATTERN: RegExp = /Mac|iPad|iPhone|iPod/;

export function ShareIcon({
  showIosIcon = defaultShouldShowIosIcon(),
  iconSize = DEFAULT_ICON_SIZE,
}: {
  showIosIcon?: boolean;
  iconSize?: number;
}) {
  return showIosIcon ? (
    <Share data-testid="iosShareIcon" size={iconSize} />
  ) : (
    <Share2 data-testid="defaultShareIcon" size={iconSize} />
  );
}

export const defaultShouldShowIosIcon = () =>
  IOS_DEVICE_PATTERN.test(navigator.userAgent) || Capacitor.getPlatform() === 'ios';

export const MemoizedShareIcon = memo(ShareIcon);
