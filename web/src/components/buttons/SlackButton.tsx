import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';
import { FaSlack } from 'react-icons/fa6';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

interface SlackButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
  isIconOnly?: boolean;
}

export function SlackButton({
  isIconOnly,
  iconSize = DEFAULT_ICON_SIZE,
  ...restProps
}: SlackButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      backgroundClasses="bg-[#4a154b]"
      foregroundClasses="text-white dark:text-white focus-visible:outline-[#4a154b]"
      href="https://slack.electricitymaps.com"
      icon={<FaSlack size={iconSize} />}
      {...restProps}
    >
      {isIconOnly ? undefined : t('button.slack')}
    </Button>
  );
}
