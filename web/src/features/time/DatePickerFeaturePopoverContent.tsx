import { atomWithStorage } from 'jotai/utils';
import { CalendarSearch } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const newDatePickerDismissedAtom = atomWithStorage(
  'newDatePickerDismissed',
  Boolean(localStorage.getItem('newDatePickerDismissed') ?? true) ?? false
);

export function DatePickerFeaturePopoverContent() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col text-left">
      <div className="flex flex-row items-center gap-2">
        <CalendarSearch size={16} />
        <h3>{t(`time-controller.new-feature-popover.title`)}</h3>
      </div>
      <p>{t(`time-controller.new-feature-popover.content`)}</p>
    </div>
  );
}
