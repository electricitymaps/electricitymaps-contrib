import { TimeAverages } from 'utils/constants';
import * as ToggleGroupPrimitive from '@radix-ui/react-toggle-group';
import { timeAverageAtom } from 'utils/state';
import { useAtom } from 'jotai';

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

function TimeAverageToggle({ className }: { className?: string }) {
  const [timeAverage, setTimeAverage] = useAtom(timeAverageAtom);
  const onToggleGroupClick = (newTimeAverage: TimeAverages) => {
    setTimeAverage(newTimeAverage);
  };

  return (
    <ToggleGroupPrimitive.Root
      className={className}
      type="multiple"
      aria-label="Font settings"
    >
      {settings.map(({ value, label, text }) => (
        <ToggleGroupPrimitive.Item
          key={`group-item-${value}-${label}`}
          value={value}
          aria-label={label}
          onClick={() => onToggleGroupClick(value)}
          className={`px-3 py-2 text-sm ${
            timeAverage === value && `rounded-full font-bold shadow-md`
          }`}
        >
          <p className="w-15 h-6 text-gray-700 dark:text-gray-100">{text}</p>
        </ToggleGroupPrimitive.Item>
      ))}
    </ToggleGroupPrimitive.Root>
  );
}

export default TimeAverageToggle;
