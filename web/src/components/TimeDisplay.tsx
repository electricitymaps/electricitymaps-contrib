import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatDate } from 'utils/formatting';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';

export function TimeDisplay({ className }: { className?: string }) {
  const { i18n } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);

  const date = new Date(selectedDatetime.datetimeString);

  return <p className={className}>{formatDate(date, i18n.language, timeAverage)}</p>;
}
