import * as ToggleGroupPrimitive from '@radix-ui/react-toggle-group';
import { TFunction } from 'i18next';
import { useTranslation } from 'react-i18next';
import { HiOutlineClock } from 'react-icons/hi2';
import { TimeAverages } from 'utils/constants';

const createOption = (time: TimeAverages, t: TFunction) => ({
  value: time,
  label: t(`time-controller.${time}`),
  dataTestId: `time-controller-${time}`,
});

export interface TimeAverageToggleProps {
  timeAverage: TimeAverages;
  onToggleGroupClick: (newTimeAverage: TimeAverages) => void;
}

function TimeAverageToggle({ timeAverage, onToggleGroupClick }: TimeAverageToggleProps) {
  const { t } = useTranslation();
  const options = Object.keys(TimeAverages).map((time) =>
    createOption(time.toLowerCase() as TimeAverages, t)
  );

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
          inline-flex select-none rounded-full px-2.5 py-2 text-sm capitalize sm:px-2 lg:px-3
            ${
              timeAverage === value
                ? 'items-center bg-white font-bold text-green-900 shadow-2xl dark:border dark:border-gray-400/10 dark:bg-gray-600 dark:text-white'
                : 'bg-gray-100 dark:bg-gray-700'
            }`}
        >
          {timeAverage === value && (
            <HiOutlineClock className="mr-1 hidden text-[0.87rem] min-[370px]:block sm:hidden xl:block" />
          )}
          <p className={`w-15 ${timeAverage === value ? '' : 'dark:opacity-80 '}`}>
            {label}
          </p>
        </ToggleGroupPrimitive.Item>
      ))}
    </ToggleGroupPrimitive.Root>
  );
}

export default TimeAverageToggle;
