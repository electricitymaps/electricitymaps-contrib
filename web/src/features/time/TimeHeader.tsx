import useGetState from 'api/getState';
import Badge from 'components/Badge';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatDate } from 'utils/formatting';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';

type TimeHeaderProps = {
  className?: string;
};
export default function TimeHeader({ className }: TimeHeaderProps) {
  const { t, i18n } = useTranslation();
  const timeAverage = useAtomValue(timeAverageAtom);
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);
  const { isLoading } = useGetState();

  const date = formatDate(selectedDatetime.datetime, i18n.language, timeAverage);

  return (
    <div
      className={`flex flex-row items-baseline justify-between sm:pb-2 ${
        className || ''
      }`}
    >
      <p className="select-none text-left font-poppins text-sm font-medium">
        {t('time-controller.title')}
      </p>
      <div
        // Setting a fixed height here to prevent the TimeHeader from jumping
        className="h-10 sm:h-8"
      >
        {!isLoading && <Badge pillText={date} type="success" />}
      </div>
    </div>
  );
}
