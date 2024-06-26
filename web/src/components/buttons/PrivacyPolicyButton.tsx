import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';

interface PrivacyPolicyButtonProps
  extends Omit<
    ButtonProps,
    | 'icon'
    | 'children'
    | 'href'
    | 'onClick'
    | 'backgroundClasses'
    | 'foregroundClasses'
    | 'type'
  > {}

export function PrivacyPolicyButton({ ...restProps }: PrivacyPolicyButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      type="link"
      href="https://www.electricitymaps.com/privacy-policy/"
      {...restProps}
    >
      {t('button.privacy-policy')}
    </Button>
  );
}
