import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';
import { FaLinkedin } from 'react-icons/fa6';
import { baseUrl, DEFAULT_ICON_SIZE } from 'utils/constants';

interface LinkedinButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
  isIconOnly?: boolean;
  isShareLink?: boolean;
}

export function LinkedinButton({
  isIconOnly,
  iconSize = DEFAULT_ICON_SIZE,
  isShareLink,
  ...restProps
}: LinkedinButtonProps) {
  const { t } = useTranslation();

  return (
    <Button
      backgroundClasses="bg-[#0A66C2]"
      foregroundClasses="text-white dark:text-white focus-visible:outline-[#0A66C2]"
      href={
        isShareLink
          ? `https://www.linkedin.com/shareArticle?mini=true&url=${baseUrl}`
          : 'https://www.linkedin.com/company/electricitymaps/'
      }
      icon={<FaLinkedin size={iconSize} />}
      {...restProps}
    >
      {isIconOnly
        ? undefined
        : t(isShareLink ? 'button.linkedin-share' : 'button.linkedin')}
    </Button>
  );
}
