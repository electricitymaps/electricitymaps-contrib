import * as ToggleGroupPrimitive from '@radix-ui/react-toggle-group';
import { HiOutlineClock } from 'react-icons/hi2';
import { TimeAverages } from 'utils/constants';

interface ToggleItem {
  value: TimeAverages;
  label: string;
  text: string;
}

const settings: ToggleItem[] = [
  {
    value: TimeAverages.HOURLY,
    label: 'hourly',
    text: '24 hours',
  },
  {
    value: TimeAverages.DAILY,
    label: 'daily',
    text: '30 days',
  },
  {
    value: TimeAverages.MONTHLY,
    label: 'monthly',
    text: '12 months',
  },
  {
    value: TimeAverages.YEARLY,
    label: 'yearly',
    text: '5 years',
  },
];

export interface TimeAverageToggleProps {
  timeAverage: TimeAverages;
  onToggleGroupClick: (newTimeAverage: TimeAverages) => void;
}

function TimeAverageToggle({ timeAverage, onToggleGroupClick }: TimeAverageToggleProps) {
  return (
    <ToggleGroupPrimitive.Root
      className={'flex-start mb-2 flex flex-row items-center gap-x-2'}
      type="multiple"
      aria-label="Font settings"
    >
      {settings.map(({ value, label, text }) => (
        <ToggleGroupPrimitive.Item
          key={`group-item-${value}-${label}`}
          value={value}
          aria-label={label}
          onClick={() => onToggleGroupClick(value)}
          className={`
          inline-flex rounded-full px-3 py-2 text-sm
            ${
              timeAverage === value
                ? 'items-center bg-white font-bold text-green-900 shadow-2xl dark:bg-gray-500 dark:text-white'
                : 'bg-gray-100 dark:bg-gray-700'
            }`}
        >
          {timeAverage === value && <HiOutlineClock className="mr-1 text-[0.87rem]" />}
          <p className="w-15">{text}</p>
        </ToggleGroupPrimitive.Item>
      ))}
    </ToggleGroupPrimitive.Root>
  );
}

export default TimeAverageToggle;
