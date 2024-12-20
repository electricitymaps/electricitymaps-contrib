import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';

interface DocsButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
}

export function DocumentationButton({ ...restProps }: DocsButtonProps) {
  const { t } = useTranslation();

  return (
    <Button href={'https://docs.electricitymaps.com/'} {...restProps}>
      {t('button.docs')}
    </Button>
  );
}
