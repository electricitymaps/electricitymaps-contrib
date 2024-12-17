import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';

interface ApiButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
}

export function ApiButton({ ...restProps }: ApiButtonProps) {
  const { t } = useTranslation();

  return (
    <Button href={'https://electricitymaps.com/pricing'} {...restProps}>
      {t('button.api')}
    </Button>
  );
}
