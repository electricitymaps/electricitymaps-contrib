import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useShare } from 'hooks/useShare';
import { t } from 'i18next';
import { Copy, Ellipsis, ShareIcon } from 'lucide-react';
import { useState } from 'react';
import { FaFacebook, FaLinkedin, FaXTwitter } from 'react-icons/fa6';
import { twMerge } from 'tailwind-merge';
import { baseUrl, DEFAULT_ICON_SIZE } from 'utils/constants';
import { hasMobileUserAgent as hasMobileUA } from 'utils/helpers';

import { DefaultCloseButton } from './AppStoreBanner';
import { TimeDisplay } from './TimeDisplay';
import { Toast, useToastReference } from './Toast';

export interface MoreOptionsDropdownProps {
  children: React.ReactElement;
  shareUrl: string;
  hasMobileUserAgent: boolean;
  isEstimated?: boolean;
}
const DURATION = 3 * 1000;
// TODO: translations
const summary = `Discover real-time electricity insights with the @electricitymaps app! ${baseUrl}`;
const preliminaryData = 'Preliminary data may change over time.';

export function MoreOptionsDropdown({
  children,
  shareUrl = baseUrl,
  hasMobileUserAgent = hasMobileUA(),
  isEstimated = false,
}: MoreOptionsDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const reference = useToastReference();
  const { copyToClipboard, share } = useShare();

  const toastMessageCallback = (message: string) => {
    setToastMessage(message);
    reference.current?.publish();
  };
  const copyShareUrl = () => copyToClipboard(shareUrl, toastMessageCallback);
  const onShare = () =>
    share(
      {
        title: 'Electricity Maps',
        text: summary,
        url: shareUrl,
      },
      toastMessageCallback
    );
  const onDismiss = () => setIsOpen(false);
  const onToggleDropdown = () => setIsOpen((previous) => !previous);

  return (
    <>
      <DropdownMenu.Root onOpenChange={onToggleDropdown} open={isOpen}>
        <DropdownMenu.Trigger>{children}</DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            className={twMerge(
              'border-gray my-2 min-w-60 rounded-2xl border border-solid bg-white shadow-md',
              hasMobileUserAgent ? 'mx-7' : '-translate-x-[42%]'
            )}
          >
            {isEstimated && (
              <div className="w-full rounded-t-2xl bg-warning/10 p-3 text-xs font-semibold text-warning dark:bg-warning-dark/10 dark:text-warning-dark">
                <p className="text-xs">{preliminaryData}</p>
              </div>
            )}
            <div className="p-3">
              <DropdownMenu.Label className="flex flex-col">
                <div className="align-items flex justify-between">
                  <h2 className="self-start text-sm">Share</h2>
                  <DefaultCloseButton onClose={onDismiss} />
                </div>
                <TimeDisplay className="whitespace-nowrap text-xs text-neutral-600" />
              </DropdownMenu.Label>
              <DropdownMenu.Separator className="my-3 h-px bg-neutral-200" />
              <DropdownMenu.Group
                className={twMerge(
                  'flex flex-col space-y-4 [&>div>p]:text-xs [&>div>p]:font-semibold [&>div]:flex [&>div]:items-center [&>div]:gap-2',
                  'space-y-4 [&>a>div>p]:text-xs [&>a>div>p]:font-semibold [&>a>div]:flex [&>a>div]:gap-2'
                )}
              >
                <DropdownMenu.Item onSelect={copyShareUrl}>
                  <Copy size={DEFAULT_ICON_SIZE} />
                  <p>Copy link to graph</p>
                </DropdownMenu.Item>
                {hasMobileUserAgent && (
                  <DropdownMenu.Item onSelect={onShare}>
                    <ShareIcon size={DEFAULT_ICON_SIZE} />
                    <p>Share via </p>
                  </DropdownMenu.Item>
                )}
                {!hasMobileUserAgent && (
                  <>
                    <a
                      href={`https://twitter.com/intent/tweet?text=${encodeURI(
                        summary
                      )}&url=${shareUrl}&hashtags=electricitymaps`}
                    >
                      <DropdownMenu.Item>
                        <FaXTwitter size={DEFAULT_ICON_SIZE} />
                        <p>Share on X (Twitter)</p>
                      </DropdownMenu.Item>
                    </a>
                    <a
                      href={`https://facebook.com/sharer/sharer.php?u=${shareUrl}&quote=${encodeURI(
                        summary
                      )}`}
                    >
                      <DropdownMenu.Item>
                        <FaFacebook size={DEFAULT_ICON_SIZE} />
                        <p>Share on Facebook</p>
                      </DropdownMenu.Item>
                    </a>
                    <a
                      href={`https://www.linkedin.com/shareArticle?mini=true&url=${shareUrl}`}
                    >
                      <DropdownMenu.Item>
                        <FaLinkedin size={DEFAULT_ICON_SIZE} />
                        <p>Share on LinkedIn</p>
                      </DropdownMenu.Item>
                    </a>
                  </>
                )}
              </DropdownMenu.Group>
            </div>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
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

export function MoreOptions({ isEstimated }: { isEstimated?: boolean }) {
  // TODO: use in individual charts
  const showMoreOptions = useFeatureFlag('more-options-dropdown');
  if (!showMoreOptions) {
    return;
  }
  return (
    <MoreOptionsDropdown isEstimated={isEstimated}>
      <Ellipsis />
    </MoreOptionsDropdown>
  );
}
