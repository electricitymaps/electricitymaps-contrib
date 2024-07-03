import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatDate } from 'utils/formatting';
import { selectedDatetimeAtom, timeAverageAtom } from 'utils/state/atoms';

export function TimeDisplay({ className }: { className?: string }) {
  const { i18n } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeAtom);

  return (
    <p className={className}>
      {formatDate(selectedDatetime, i18n.language, timeAverage)}
    </p>
  );
}
