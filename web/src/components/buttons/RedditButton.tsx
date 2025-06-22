import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';
import { FaReddit } from 'react-icons/fa6';
import { baseUrl, DEFAULT_ICON_SIZE } from 'utils/constants';

interface RedditButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
  isIconOnly?: boolean;
  isShareLink?: boolean;
}

export function RedditButton({
  isIconOnly,
  iconSize = DEFAULT_ICON_SIZE,
  isShareLink,
  ...restProps
}: RedditButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      backgroundClasses="bg-[#FF4500]"
      foregroundClasses="text-white dark:text-white focus-visible:outline-[#0A66C2]"
      href={
        isShareLink
          ? `https://www.reddit.com/web/submit?url=${baseUrl}`
          : 'https://www.reddit.com/r/electricitymaps/'
      }
      icon={<FaReddit size={iconSize} />}
      {...restProps}
    >
      {isIconOnly
        ? undefined
        : t(($) => (isShareLink ? $.button['reddit-share'] : $.button.reddit))}
    </Button>
  );
}
