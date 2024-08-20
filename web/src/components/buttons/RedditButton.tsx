import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';
import { FaReddit } from 'react-icons/fa6';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

interface RedditButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
  isIconOnly?: boolean;
}

export function RedditButton({
  isIconOnly,
  iconSize = DEFAULT_ICON_SIZE,
  ...restProps
}: RedditButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      backgroundClasses="bg-[#FF4500]"
      foregroundClasses="text-white dark:text-white focus-visible:outline-[#0A66C2]"
      href={'https://www.reddit.com/r/electricitymaps/'}
      icon={<FaReddit size={iconSize} />}
      {...restProps}
    >
      {isIconOnly ? undefined : t('button.reddit')}
    </Button>
  );
}
