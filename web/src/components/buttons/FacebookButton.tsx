import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';
import { FaFacebook } from 'react-icons/fa6';
import { baseUrl, DEFAULT_ICON_SIZE } from 'utils/constants';

interface FacebookButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
  isIconOnly?: boolean;
  isShareLink?: boolean;
}

export function FacebookButton({
  isIconOnly,
  iconSize = DEFAULT_ICON_SIZE,
  isShareLink,
  ...restProps
}: FacebookButtonProps) {
  const { t } = useTranslation();

  return (
    <Button
      backgroundClasses="bg-[#1877F2]"
      foregroundClasses="text-white dark:text-white focus-visible:outline-[#1877F2]"
      href={
        isShareLink
          ? `https://facebook.com/sharer/sharer.php?u=${baseUrl}`
          : 'https://www.facebook.com/electricitymaps/'
      }
      icon={<FaFacebook size={iconSize} />}
      {...restProps}
    >
      {isIconOnly
        ? undefined
        : t(isShareLink ? 'button.facebook-share' : 'button.facebook')}
    </Button>
  );
}
