import { X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { twMerge } from 'tailwind-merge';
import { DEFAULT_ICON_SIZE } from 'utils/constants';

export interface DefaultCloseButtonProps {
  onClose(): void;
  color?: 'gray' | 'black';
}

export function DefaultCloseButton({
  onClose,
  color = 'black',
}: DefaultCloseButtonProps) {
  const { t } = useTranslation();
  return (
    <button
      aria-label={t('misc.dismiss')}
      data-testid="dismiss-btn"
      onClick={onClose}
      className={twMerge(
        'pointer-events-auto flex items-center justify-center self-center',
        color === 'gray'
          ? 'text-neutral-400 dark:text-neutral-300'
          : 'text-black dark:text-white'
      )}
    >
      <X size={DEFAULT_ICON_SIZE} />
    </button>
  );
}
