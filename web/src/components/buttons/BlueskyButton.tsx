import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';
import { FaBluesky } from 'react-icons/fa6';
import { ShareType, trackShare } from 'utils/analytics';
import { baseUrl, DEFAULT_ICON_SIZE } from 'utils/constants';

interface BlueskyButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
  isIconOnly?: boolean;
  isShareLink?: boolean;
}
const trackBlueskyShare = trackShare(ShareType.BLUESKY);

export function BlueskyButton({
  isIconOnly,
  iconSize = DEFAULT_ICON_SIZE,
  isShareLink,
  ...restProps
}: BlueskyButtonProps) {
  const { t } = useTranslation();

  return (
    <Button
      backgroundClasses="bg-[#1185fe]"
      foregroundClasses="text-white dark:text-white focus-visible:outline-[#1185fe]"
      href={
        isShareLink
          ? `https://bsky.app/intent/compose?text=${t('button.bluesky-share', {
              baseUrl,
            })}`
          : undefined
      }
      onClick={isShareLink ? trackBlueskyShare : undefined}
      icon={<FaBluesky size={iconSize} />}
      {...restProps}
    >
      {isIconOnly
        ? undefined
        : t(isShareLink ? 'button.Bluesky-share' : 'button.Bluesky')}
    </Button>
  );
}
