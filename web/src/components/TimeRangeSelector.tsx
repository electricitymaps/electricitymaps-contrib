import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useFeatureFlag } from 'features/feature-flags/api';
import { TFunction } from 'i18next';
import { ChevronsUpDown } from 'lucide-react';
import { memo, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { TimeRange } from 'utils/constants';

import { useDropdownCtl } from './MoreOptionsDropdown';

const createOption = (
  time: TimeRange,
  t: TFunction,
  historicalLinkingEnabled: boolean
) => ({
  value: time,
  label: t(
    `time-controller.${historicalLinkingEnabled ? 'historical-linking.' : ''}${time}`
  ),
  dataTestId: `time-controller-${time}`,
});

export interface TimeRangeSelectorProps {
  timeRange: TimeRange;
  onToggleGroupClick: (newTimeRange: TimeRange) => void;
}

function TimeRangeSelector({ timeRange, onToggleGroupClick }: TimeRangeSelectorProps) {
  const { t } = useTranslation();
  const { isOpen, onDismiss, onToggleDropdown } = useDropdownCtl();
  const historicalLinkingEnabled = useFeatureFlag('historical-linking');

  const options = useMemo(
    () =>
      Object.values(TimeRange).map((value) =>
        createOption(value, t, historicalLinkingEnabled)
      ),
    [historicalLinkingEnabled, t]
  );

  const selectedLabel =
    timeRange.length > 3
      ? options.find((opt) => opt.value === timeRange)!.label.slice(0, 5)
      : timeRange;

  return (
    <DropdownMenu.Root onOpenChange={onToggleDropdown} open={isOpen} modal={false}>
      <DropdownMenu.Trigger>
        <div className="flex flex-row items-center gap-1 rounded-xl p-1 pl-2 text-sm font-semibold capitalize outline outline-1 outline-neutral-200">
          {selectedLabel}
          <ChevronsUpDown height="14px" />
        </div>
      </DropdownMenu.Trigger>
      <DropdownMenu.Content className="border-1 rounded-xl border border-neutral-200 bg-white p-1">
        {options.map(({ value, label, dataTestId }) => (
          <DropdownMenu.Item
            key={`group-item-${value}-${label}`}
            data-testid={dataTestId}
            value={value}
            aria-label={label}
            onClick={() => onToggleGroupClick(value)}
            className={`h-full grow basis-0 select-none rounded-xl p-2 text-xs font-semibold capitalize hover:bg-neutral-100 focus-visible:outline-none`}
          >
            {label}
          </DropdownMenu.Item>
        ))}
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  );
}

export default memo(TimeRangeSelector);
