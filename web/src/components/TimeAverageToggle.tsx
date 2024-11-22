import {
  Item as ToggleGroupItem,
  Root as ToggleGroupRoot,
} from '@radix-ui/react-toggle-group';
import { useFeatureFlag } from 'features/feature-flags/api';
import { TFunction } from 'i18next';
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { TimeAverages } from 'utils/constants';

const createOption = (
  time: TimeAverages,
  t: TFunction,
  historicalLinkingEnabled: boolean
) => ({
  value: time,
  label: t(
    `time-controller.${historicalLinkingEnabled ? 'historical-linking.' : ''}${time}`
  ),
  dataTestId: `time-controller-${time}`,
});

export interface TimeAverageToggleProps {
  timeAverage: TimeAverages;
  onToggleGroupClick: (newTimeAverage: TimeAverages) => void;
}

function TimeAverageToggle({ timeAverage, onToggleGroupClick }: TimeAverageToggleProps) {
  const { t } = useTranslation();
  const historicalLinkingEnabled = useFeatureFlag('historical-linking');
  const options = useMemo(
    () =>
      Object.values(TimeAverages).map((value) =>
        createOption(value, t, historicalLinkingEnabled)
      ),
    [t, historicalLinkingEnabled]
  );

  return (
    <ToggleGroupRoot
      className={
        'mt-1 flex h-11 min-w-fit grow items-center justify-between gap-1 rounded-full bg-gray-300/50 p-1 dark:bg-gray-700/50'
      }
      type="multiple"
      aria-label="Toggle between time averages"
    >
      {options.map(({ value, label, dataTestId }) => (
        <ToggleGroupItem
          key={`group-item-${value}-${label}`}
          data-test-id={dataTestId}
          value={value}
          aria-label={label}
          onClick={() => onToggleGroupClick(value)}
          className={`
          h-full grow basis-0 select-none rounded-full text-xs font-semibold capitalize
            ${
              timeAverage === value
                ? 'bg-white/80 text-brand-green outline outline-1 outline-neutral-200 dark:bg-gray-600/80 dark:text-white dark:outline-gray-400/10'
                : ''
            }
            focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-2 focus-visible:outline-brand-green`}
        >
          {label}
        </ToggleGroupItem>
      ))}
    </ToggleGroupRoot>
  );
}

export default TimeAverageToggle;
