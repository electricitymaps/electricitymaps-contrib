import { Share as CapShare, ShareOptions } from '@capacitor/share';
import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { ShareType, trackShare } from 'utils/analytics';

const trackShareClick = trackShare(ShareType.SHARE);
const trackShareCompletion = trackShare(ShareType.COMPLETED_SHARE);
const SHARE_ERROR_PATTERN: RegExp = /AbortError|canceled/;

export function useShare() {
  const { t } = useTranslation();

  const copyToClipboard = useCallback(
    async (url: string, callback?: (argument: string) => void) => {
      try {
        await navigator.clipboard.writeText(url);
        trackShareClick();
        callback?.(t('share-button.clipboard'));
      } catch (error) {
        console.error(error);
        callback?.(t('share-button.clipboard-error'));
      }
    },
    [t]
  );

  const share = useCallback(
    async (shareData: ShareOptions, callback?: (argument: string) => void) => {
      try {
        trackShareClick();
        const result = await CapShare.share(shareData);
        if (result) {
          trackShareCompletion();
        }
        return result;
      } catch (error) {
        if (error instanceof Error && !SHARE_ERROR_PATTERN.test(error.toString())) {
          console.error(error);
          callback?.(t('share-button.share-error'));
        }
        return;
      }
    },
    [t]
  );

  return {
    share,
    copyToClipboard,
  };
}
