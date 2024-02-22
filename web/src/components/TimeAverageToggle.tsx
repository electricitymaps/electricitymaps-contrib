import * as ToggleGroupPrimitive from '@radix-ui/react-toggle-group';
import { HiOutlineClock } from 'react-icons/hi2';
import { TranslationFunction, useTranslation } from 'translation/translation';
import { TimeAverages } from 'utils/constants';

const createOption = (time: TimeAverages, __: TranslationFunction) => ({
  value: time,
  label: __(`time-controller.${time}`),
  dataTestId: `time-controller-${time}`,
});

export interface TimeAverageToggleProps {
  timeAverage: TimeAverages;
  onToggleGroupClick: (newTimeAverage: TimeAverages) => void;
}

function TimeAverageToggle({ timeAverage, onToggleGroupClick }: TimeAverageToggleProps) {
  const { __ } = useTranslation();
  const options = Object.keys(TimeAverages).map((time) =>
    createOption(time.toLowerCase() as TimeAverages, __)
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
