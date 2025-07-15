import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useFeatureFlag } from 'features/feature-flags/api';
import { TFunction } from 'i18next';
import { ChevronsUpDown, FlaskConicalIcon } from 'lucide-react';
import { memo, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { TimeRange } from 'utils/constants';

import { useDropdownCtl } from './MoreOptionsDropdown';

const createOption = (time: TimeRange, t: TFunction) => ({
  value: time,
  label: t(`time-controller.${time}`),
  dataTestId: `time-controller-${time}`,
  isExperimental: time === TimeRange.H24,
});

export interface TimeRangeSelectorProps {
  timeRange: TimeRange;
  onToggleGroupClick: (newTimeRange: TimeRange) => void;
}

function TimeRangeSelector({ timeRange, onToggleGroupClick }: TimeRangeSelectorProps) {
  const { t } = useTranslation();
  const { isOpen, onToggleDropdown } = useDropdownCtl();
  const is5MinGranularityEnabled = useFeatureFlag('five-minute-granularity');

  const options = useMemo(
    () =>
      Object.values(TimeRange)
        .filter((value) => {
          if (!is5MinGranularityEnabled && value === TimeRange.H24) {
            return false;
          }
          return true;
        })
        .map((value) => ({
          ...createOption(value, t),
          onClick: () => onToggleGroupClick(value),
        })),
    [is5MinGranularityEnabled, t, onToggleGroupClick]
  );

  const selectedLabel = useMemo(
    () => options.find(({ value }) => value === timeRange)?.label,
    [options, timeRange]
  );

  return (
    <DropdownMenu.Root onOpenChange={onToggleDropdown} open={isOpen} modal={false}>
      <DropdownMenu.Trigger>
        <div className="flex w-32 flex-row items-center justify-between rounded-xl bg-white p-1 pl-2 text-sm font-semibold capitalize outline outline-1 outline-neutral-200 hover:bg-neutral-100 dark:bg-neutral-900 dark:outline-neutral-700 dark:hover:bg-neutral-800">
          {selectedLabel}
          <ChevronsUpDown height="14px" />
        </div>
      </DropdownMenu.Trigger>
      <DropdownMenu.Content
        sideOffset={4}
        className="border-1 z-50 w-32 rounded-xl border border-neutral-200 bg-white p-1 dark:border-neutral-700 dark:bg-neutral-900"
      >
        {options.map(({ value, label, dataTestId, onClick, isExperimental }) => (
          <DropdownMenu.Item
            key={`group-item-${value}-${label}`}
            data-testid={dataTestId}
            aria-label={label}
            onClick={onClick}
            className={`flex select-none items-center justify-between rounded-xl p-2 text-xs font-semibold capitalize hover:bg-neutral-100 focus-visible:outline-none dark:hover:bg-neutral-800`}
          >
            {label} {isExperimental && <FlaskConicalIcon size={12} />}
          </DropdownMenu.Item>
        ))}
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  );
}

export default memo(TimeRangeSelector);
