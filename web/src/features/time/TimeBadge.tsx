import useGetState from 'api/getState';
import Badge from 'components/Badge';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatDate } from 'utils/formatting';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';

export default function TimeBadge() {
  const { i18n } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const { isLoading } = useGetState();

  const formattedDate = formatDate(
    new Date(selectedDatetime.datetimeString),
    i18n.language,
    timeAverage
  );

  return !isLoading && <Badge pillText={formattedDate} type="success" />;
}
