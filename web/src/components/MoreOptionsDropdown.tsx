import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useShare } from 'hooks/useShare';
import { useAtomValue } from 'jotai';
import { Link } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaFacebook, FaLinkedin, FaReddit, FaSquareXTwitter } from 'react-icons/fa6';
import { twMerge } from 'tailwind-merge';
import { getTrackByShareType, ShareType } from 'utils/analytics';
import {
  baseUrl,
  Charts,
  DEFAULT_ICON_SIZE,
  DEFAULT_TOAST_DURATION,
} from 'utils/constants';
import { hasMobileUserAgent as hasMobileUA } from 'utils/helpers';
import { displayByEmissionsAtom, isHourlyAtom } from 'utils/state/atoms';

import { DefaultCloseButton } from './DefaultCloseButton';
import { MemoizedShareIcon } from './ShareIcon';
import { TimeDisplay } from './TimeDisplay';
import { Toast, useToastReference } from './Toast';

export interface MoreOptionsDropdownProps {
  children: React.ReactElement;
  shareUrl?: string;
  hasMobileUserAgent?: boolean;
  isEstimated?: boolean;
  id: Charts | 'zone';
}

const dropdownItemStyle = 'flex items-center gap-2 py-2';
const dropdownContentStyle = 'font-semibold text-xs';

export function MoreOptionsDropdown({
  children,
  shareUrl = baseUrl,
  hasMobileUserAgent = hasMobileUA(),
  isEstimated = false,
  id,
}: MoreOptionsDropdownProps) {
  const { t } = useTranslation();
  const [toastMessage, setToastMessage] = useState('');
  const { isOpen, onDismiss, onToggleDropdown } = useDropdownCtl();
  const reference = useToastReference();
  const { copyToClipboard, share } = useShare();

  const summary = `${t('more-options-dropdown.summary')} ${baseUrl}`;

  const handleTrackShares = getTrackByShareType(id);

  const { onShare, copyShareUrl } = useMemo(() => {
    const toastMessageCallback = (message: string) => {
      setToastMessage(message);
      reference.current?.publish();
    };

    return {
      copyShareUrl: () => {
        copyToClipboard(shareUrl, toastMessageCallback);
        handleTrackShares[ShareType.COPY]();
      },
      onShare: () => {
        share(
          {
            title: 'Electricity Maps',
            text: summary,
            url: shareUrl,
          },
          toastMessageCallback
        );
        handleTrackShares[ShareType.SHARE]();
      },
    };
  }, [reference, shareUrl, summary, share, copyToClipboard, handleTrackShares]);

  const title =
    id === 'zone'
      ? t(`more-options-dropdown.zone-title`)
      : t(`more-options-dropdown.chart-title`);

  const copyLinkText =
    id === 'zone'
      ? t(`more-options-dropdown.copy-zone-link`)
      : t(`more-options-dropdown.copy-chart-link`);

  return (
    <>
      <DropdownMenu.Root onOpenChange={onToggleDropdown} open={isOpen} modal={false}>
        <DropdownMenu.Trigger>{children}</DropdownMenu.Trigger>
        <DropdownMenu.Content
          className={twMerge(
            'border-gray z-30 my-2 min-w-60 rounded-2xl border border-solid bg-white shadow-md dark:border-b dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300',
            hasMobileUserAgent ? 'mx-7' : '-translate-x-[42%]'
          )}
        >
          {isEstimated && (
            <div className="w-full rounded-t-2xl bg-warning/10 p-3 text-xs font-semibold text-warning dark:bg-warning-dark/10 dark:text-warning-dark">
              <p className="text-xs">{t('more-options-dropdown.preliminary-data')}</p>
            </div>
          )}
          <div className="px-3 pb-2 pt-3">
            <DropdownMenu.Label className="flex flex-col">
              <div className="align-items flex justify-between">
                <h2 className="self-start text-sm">{title}</h2>
                <DefaultCloseButton onClose={onDismiss} />
              </div>
              <TimeDisplay className="whitespace-nowrap text-xs font-normal text-neutral-600 dark:text-gray-300" />
            </DropdownMenu.Label>
            <DropdownMenu.Separator className="mb-1 mt-3 h-px bg-neutral-200 dark:bg-gray-700" />
            <DropdownMenu.Group className="flex cursor-pointer flex-col">
              <DropdownMenu.Item className={dropdownItemStyle} onSelect={copyShareUrl}>
                <Link size={DEFAULT_ICON_SIZE} />
                <p className={dropdownContentStyle}>{copyLinkText}</p>
              </DropdownMenu.Item>
              {hasMobileUserAgent && (
                <DropdownMenu.Item className={dropdownItemStyle} onSelect={onShare}>
                  <MemoizedShareIcon />
                  <p className={dropdownContentStyle}>
                    {t('more-options-dropdown.mobile-share-via')}
                  </p>
                </DropdownMenu.Item>
              )}
              {!hasMobileUserAgent && (
                <>
                  <a
                    data-test-id="twitter-chart-share"
                    target="_blank"
                    rel="noopener"
                    onClick={handleTrackShares[ShareType.TWITTER]}
                    href={`https://twitter.com/intent/tweet?&url=${shareUrl}&text=${encodeURI(
                      summary
                    )}&hashtags=electricitymaps`}
                  >
                    <DropdownMenu.Item className={dropdownItemStyle}>
                      <FaSquareXTwitter size={DEFAULT_ICON_SIZE} />
                      <p className={dropdownContentStyle}>{t('button.twitter-share')}</p>
                    </DropdownMenu.Item>
                  </a>
                  <a
                    data-test-id="facebook-chart-share"
                    target="_blank"
                    rel="noopener"
                    onClick={handleTrackShares[ShareType.FACEBOOK]}
                    href={`https://facebook.com/sharer/sharer.php?u=${shareUrl}&quote=${encodeURI(
                      summary
                    )}`}
                  >
                    <DropdownMenu.Item className={dropdownItemStyle}>
                      <FaFacebook size={DEFAULT_ICON_SIZE} />
                      <p className={dropdownContentStyle}>{t('button.facebook-share')}</p>
                    </DropdownMenu.Item>
                  </a>
                  <a
                    data-test-id="linkedin-chart-share"
                    href={`https://www.linkedin.com/shareArticle?mini=true&url=${shareUrl}`}
                    target="_blank"
                    rel="noopener"
                    onClick={handleTrackShares[ShareType.LINKEDIN]}
                  >
                    <DropdownMenu.Item className={dropdownItemStyle}>
                      <FaLinkedin size={DEFAULT_ICON_SIZE} />
                      <p className={dropdownContentStyle}>{t('button.linkedin-share')}</p>
                    </DropdownMenu.Item>
                  </a>
                  <a
                    data-test-id="reddit-chart-share"
                    href={`https://www.reddit.com/web/submit?url=${shareUrl}`}
                    target="_blank"
                    rel="noopener"
                    onClick={handleTrackShares[ShareType.REDDIT]}
                  >
                    <DropdownMenu.Item className={dropdownItemStyle}>
                      <FaReddit size={DEFAULT_ICON_SIZE} />
                      <p className={dropdownContentStyle}>{t('button.reddit-share')}</p>
                    </DropdownMenu.Item>
                  </a>
                </>
              )}
            </DropdownMenu.Group>
          </div>
        </DropdownMenu.Content>
      </DropdownMenu.Root>
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

const useDropdownCtl = () => {
  const [isOpen, setIsOpen] = useState(false);
  const methods = useMemo(
    () => ({
      onDismiss: () => setIsOpen(false),
      onToggleDropdown: () => setIsOpen((previous) => !previous),
    }),
    [setIsOpen]
  );

  return { isOpen, ...methods };
};

export function useShowMoreOptions() {
  const isMoreOptionsEnabled = useFeatureFlag('more-options-dropdown');
  const isHourly = useAtomValue(isHourlyAtom);
  const displayByEmissions = useAtomValue(displayByEmissionsAtom);
  const showMoreOptions = isMoreOptionsEnabled && isHourly && !displayByEmissions;

  return showMoreOptions;
}
