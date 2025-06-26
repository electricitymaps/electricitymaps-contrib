import { Button, ButtonProps } from 'components/Button';
import { FileText } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

interface DocsButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
}

export function DocumentationButton({
  iconSize = DEFAULT_ICON_SIZE,
  ...restProps
}: DocsButtonProps) {
  const { t } = useTranslation();

  return (
    <Button
      href={'https://docs.electricitymaps.com/'}
      {...restProps}
      icon={<FileText size={iconSize} />}
    >
      {t(($) => $.button.docs)}
    </Button>
  );
}
