import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatDate } from 'utils/formatting';
import { selectedDatetimeStringAtom, timeAverageAtom } from 'utils/state/atoms';

export function TimeDisplay({ className }: { className?: string }) {
  const { i18n } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);

  const date = new Date(selectedDatetimeString);

  return <p className={className}>{formatDate(date, i18n.language, timeAverage)}</p>;
}
