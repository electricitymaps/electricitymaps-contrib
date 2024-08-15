import { Button, ButtonProps } from 'components/Button';
import { CloudCog } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

interface CommercialApiButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'type' | 'onClick' | 'foregroundClasses'
  > {
  iconSize?: number;
  type?: 'primary' | 'link';
}

export function CommercialApiButton({
  iconSize = DEFAULT_ICON_SIZE,
  type,
  ...restProps
}: CommercialApiButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      icon={<CloudCog size={iconSize} />}
      type={type}
      href="https://electricitymaps.com/?utm_source=app.electricitymaps.com&utm_medium=referral&utm_campaign=country_panel"
      {...restProps}
    >
      {t('header.get-data')}
    </Button>
  );
}
