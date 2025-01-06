import { Button, ButtonProps } from 'components/Button';
import { CloudCog } from 'lucide-react';
import { memo } from 'react';
import { useTranslation } from 'react-i18next';

interface ApiButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'type' | 'onClick' | 'foregroundClasses'
  > {
  iconSize?: number;
  type?: 'primary' | 'link' | 'secondary';
}

function ApiButton({ iconSize = 20, type, ...restProps }: ApiButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      icon={<CloudCog size={iconSize} />}
      type={type}
      href="https://electricitymaps.com/pricing?utm_source=app.electricitymaps.com&utm_medium=referral&utm_campaign=api-cta"
      {...restProps}
    >
      {t('button.api')}
    </Button>
  );
}

export default memo(ApiButton);
