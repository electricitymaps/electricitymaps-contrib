import { Button, ButtonProps } from 'components/Button';
import { useTranslation } from 'react-i18next';
import { FaCommentDots } from 'react-icons/fa6';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

interface FeedbackButtonProps
  extends Omit<
    ButtonProps,
    'icon' | 'children' | 'href' | 'onClick' | 'backgroundClasses' | 'foregroundClasses'
  > {
  iconSize?: number;
  isIconOnly?: boolean;
}

export function FeedbackButton({
  isIconOnly,
  iconSize = DEFAULT_ICON_SIZE,
  ...restProps
}: FeedbackButtonProps) {
  const { t } = useTranslation();
  return (
    <Button
      href="https://forms.gle/VHaeHzXyGodFKZY18"
      icon={<FaCommentDots size={iconSize} />}
      {...restProps}
    >
      {isIconOnly ? undefined : t('button.feedback')}
    </Button>
  );
}
