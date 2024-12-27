import { Button, ButtonProps } from 'components/Button';
import { CloudCog } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface CommercialApiButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'type' | 'onClick' | 'foregroundClasses'
  > {
  iconSize?: number;
  type?: 'primary' | 'link' | 'secondary';
}

export function CommercialApiButton({
  iconSize = 20,
  type,
  ...restProps
}: CommercialApiButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      icon={<CloudCog size={iconSize} />}
      type={type}
      href="https://electricitymaps.com/get-our-data?utm_source=app.electricitymaps.com&utm_medium=referral&utm_campaign=country_panel"
      {...restProps}
    >
      {t('header.get-data')}
    </Button>
  );
}
