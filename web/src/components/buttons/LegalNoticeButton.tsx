import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';

interface LegalNoticeButtonProps
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

export function LegalNoticeButton({ ...restProps }: LegalNoticeButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      type="link"
      href="https://www.electricitymaps.com/legal-notice/"
      {...restProps}
    >
      {t(($) => $.button['legal-notice'])}
    </Button>
  );
}
