import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatDate } from 'utils/formatting';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';

export function TimeDisplay({ className }: { className?: string }) {
  const { i18n } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);

  return (
    <p className={className}>
      {formatDate(selectedDatetime.datetime, i18n.language, timeAverage)}
    </p>
  );
}
