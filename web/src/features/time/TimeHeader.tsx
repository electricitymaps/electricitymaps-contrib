import useGetState from 'api/getState';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { formatDate } from 'utils/formatting';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';

type TimeHeaderProps = {
  className?: string;
};
export default function TimeHeader({ className }: TimeHeaderProps) {
  const { t, i18n } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const { isLoading } = useGetState();

  const date = formatDate(
    new Date(selectedDatetime.datetimeString),
    i18n.language,
    timeAverage
  );

  return (
    <div
      className={`flex flex-row items-baseline justify-between sm:pb-2 ${
        className || ''
      }`}
    >
      <p className="select-none text-left text-base font-bold">
        {t('time-controller.title')}
      </p>
      <div
        // Setting a fixed height here to prevent the TimeHeader from jumping
        className="h-10 sm:h-8"
      >
        {!isLoading && (
          <div className="select-none whitespace-nowrap rounded-full bg-brand-green/10 px-2 py-1 text-sm text-brand-green lg:px-3 dark:bg-gray-700 dark:text-white">
            {date}
          </div>
        )}
      </div>
    </div>
  );
}
