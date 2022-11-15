import * as ToggleGroupPrimitive from '@radix-ui/react-toggle-group';
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

function ClockIcon() {
  return <span className="material-symbols-outlined mr-1 text-[0.87rem]">schedule</span>;
}

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
          className={
            timeAverage === value
              ? 'inline-flex items-center rounded-full bg-white px-3 py-2 text-sm font-bold text-green-900 shadow-2xl dark:bg-gray-500 dark:text-white'
              : 'inline-flex rounded-full bg-gray-100 px-3 py-2 text-sm dark:bg-gray-700'
          }
        >
          {timeAverage === value && <ClockIcon />}
          <p className="w-15">{text}</p>
        </ToggleGroupPrimitive.Item>
      ))}
    </ToggleGroupPrimitive.Root>
  );
}

export default TimeAverageToggle;
