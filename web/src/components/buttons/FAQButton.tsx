import { Button, ButtonProps } from 'components/Button';
import { isFAQModalOpenAtom } from 'features/modals/modalAtoms';
import { useSetAtom } from 'jotai';
import { Info } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

interface FAQButtonProps
  extends Omit<
    ButtonProps,
    | 'icon'
    | 'children'
    | 'href'
    | 'onClick'
    | 'backgroundClasses'
    | 'foregroundClasses'
    | 'type'
  > {
  iconSize?: number;
  isIconOnly?: boolean;
}

export function FAQButton({
  isIconOnly,
  iconSize = DEFAULT_ICON_SIZE,
  ...restProps
}: FAQButtonProps) {
  const { t } = useTranslation();
  const setIsFAQModalOpen = useSetAtom(isFAQModalOpenAtom);
  return (
    <Button
      type="secondary"
      icon={<Info size={iconSize} />}
      onClick={() => setIsFAQModalOpen(true)}
      {...restProps}
    >
      {isIconOnly ? undefined : t('button.faq')}
    </Button>
  );
}
