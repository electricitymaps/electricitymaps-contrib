import useGetState from 'api/getState';
import Badge from 'components/Badge';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatDate } from 'utils/formatting';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';

export default function TimeBadge() {
  const { i18n } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);
  const { isLoading } = useGetState();

  const formattedDate = formatDate(selectedDatetime.datetime, i18n.language, timeAverage);

  return !isLoading && <Badge pillText={formattedDate} type="success" />;
}
