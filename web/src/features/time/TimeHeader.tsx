import useGetState from 'api/getState';
import Badge from 'components/Badge';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatDate } from 'utils/formatting';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';

export default function TimeHeader() {
  const { t, i18n } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);
  const { isLoading } = useGetState();

  const date = formatDate(selectedDatetime.datetime, i18n.language, timeAverage);

  return (
    <div className="flex min-h-6 flex-row items-center">
      <h3 className="grow select-none text-left">
        {t(`time-controller.title.${timeAverage}`)}
      </h3>
      {!isLoading && <Badge pillText={date} type="success" />}
    </div>
  );
}
