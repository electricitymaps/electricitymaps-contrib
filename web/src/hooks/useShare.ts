import { Share as CapShare, ShareOptions } from '@capacitor/share';
import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';

const SHARE_ERROR_PATTERN: RegExp = /AbortError|canceled/;

export function useShare() {
  const { t } = useTranslation();

  const copyToClipboard = useCallback(
    async (url: string, callback?: (argument: string) => void) => {
      try {
        await navigator.clipboard.writeText(url);
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
        const result = await CapShare.share(shareData);
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
