import * as ToggleGroupPrimitive from '@radix-ui/react-toggle-group';
import { HiOutlineClock } from 'react-icons/hi2';
import { useTranslation } from 'translation/translation';
import { TimeAverages } from 'utils/constants';
import { formatTimeRange } from 'utils/formatting';

interface ToggleItem {
  value: TimeAverages;
  label: string;
  dataTestId: string; // For testing with Cypress
}

const getOptions = (language: string): ToggleItem[] => [
  {
    value: TimeAverages.HOURLY,
    label: formatTimeRange(language, TimeAverages.HOURLY),
    dataTestId: 'time-controller-hourly',
  },
  {
    value: TimeAverages.DAILY,
    label: formatTimeRange(language, TimeAverages.DAILY),
    dataTestId: 'time-controller-daily',
  },
  {
    value: TimeAverages.MONTHLY,
    label: formatTimeRange(language, TimeAverages.MONTHLY),
    dataTestId: 'time-controller-monthly',
  },
  {
    value: TimeAverages.YEARLY,
    label: formatTimeRange(language, TimeAverages.YEARLY),
    dataTestId: 'time-controller-yearly',
  },
];

export interface TimeAverageToggleProps {
  timeAverage: TimeAverages;
  onToggleGroupClick: (newTimeAverage: TimeAverages) => void;
}

function TimeAverageToggle({ timeAverage, onToggleGroupClick }: TimeAverageToggleProps) {
  const { i18n } = useTranslation();
  const options = getOptions(i18n.language);
  return (
    <ToggleGroupPrimitive.Root
      className={
        'flex-start mb-2 flex flex-row items-center gap-x-2 md:gap-x-1.5 lg:gap-x-2'
      }
      type="multiple"
      aria-label="Font settings"
    >
      {options.map(({ value, label, dataTestId }) => (
        <ToggleGroupPrimitive.Item
          key={`group-item-${value}-${label}`}
          data-test-id={dataTestId}
          value={value}
          aria-label={label}
          onClick={() => onToggleGroupClick(value)}
          className={`
          inline-flex select-none rounded-full px-2.5 py-2 text-sm sm:px-2 lg:px-3
            ${
              timeAverage === value
                ? 'items-center bg-white font-bold text-green-900 shadow-2xl dark:bg-gray-500 dark:text-white'
                : 'bg-gray-100 dark:bg-gray-700'
            }`}
        >
          {timeAverage === value && (
            <HiOutlineClock className="mr-1 hidden text-[0.87rem] min-[370px]:block sm:hidden xl:block" />
          )}
          <p className="w-15">{label}</p>
        </ToggleGroupPrimitive.Item>
      ))}
    </ToggleGroupPrimitive.Root>
  );
}

export default TimeAverageToggle;
