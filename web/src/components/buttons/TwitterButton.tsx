import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';
import { FaXTwitter } from 'react-icons/fa6';
import { baseUrl, DEFAULT_ICON_SIZE } from 'utils/constants';

interface TwitterButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
  isIconOnly?: boolean;
  isShareLink?: boolean;
}

export function TwitterButton({
  isIconOnly,
  iconSize = DEFAULT_ICON_SIZE,
  isShareLink,
  ...restProps
}: TwitterButtonProps) {
  const { t } = useTranslation();

  return (
    <Button
      backgroundClasses="bg-black"
      foregroundClasses="text-white dark:text-white focus-visible:outline-black"
      href={isShareLink ? `https://twitter.com/intent/tweet?url=${baseUrl}` : undefined}
      icon={<FaXTwitter size={iconSize} />}
      {...restProps}
    >
      {isIconOnly
        ? undefined
        : t(isShareLink ? 'button.twitter-share' : 'button.twitter')}
    </Button>
  );
}
