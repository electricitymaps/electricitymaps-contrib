import useGetState from 'api/getState';
import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { formatDate } from 'utils/formatting';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';

type TimeHeaderProps = {
  className?: string;
};
export default function TimeHeader({ className }: TimeHeaderProps) {
  const { __, i18n } = useTranslation();
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
      className={`flex flex-row items-center justify-between sm:pb-2 ${className || ''}`}
    >
      <p className="select-none text-base font-bold">{__('time-controller.title')}</p>
      <div
        // Setting a fixed height here to prevent the TimeHeader from jumping
        className="h-10 sm:h-8"
      >
        {!isLoading && (
          <div className="select-none rounded-full bg-brand-green/10 py-2 px-3 text-xs text-brand-green dark:bg-gray-700 dark:text-white">
            {date}
          </div>
        )}
      </div>
    </div>
  );
}
