import type { Meta, StoryObj } from '@storybook/react';
import { zoneStateMock } from 'stories/mockData';

import { TooltipInner } from './MapTooltip';

function TestWrapper({
  zoneKey = 'DK-DK2',
  estimationMethod = undefined,
  hasOutage = undefined,
  co2intensity,
  fossilFuelRatio,
  renewableRatio,
}: {
  zoneKey?: string;
  estimationMethod?: string;
  hasOutage?: boolean;
  co2intensity: number;
  fossilFuelRatio: number;
  renewableRatio: number;
}) {
  return (
    <div className="pointer-events-none relative w-[361px] rounded-2xl border border-neutral-200 bg-white text-sm shadow-lg dark:border-gray-700 dark:bg-gray-900 ">
      <div>
        <TooltipInner
          zoneData={{
            ...zoneStateMock,
            co2intensity,
            fossilFuelRatio,
            renewableRatio,
            estimationMethod,
            hasOutage,
          }}
          zoneId={zoneKey}
          date={'2022-01-01'}
        />
      </div>
    </div>
  );
}

const meta: Meta<typeof TestWrapper> = {
  title: 'Modal/MapTooltip',
  component: TestWrapper,
};

export default meta;
type Story = StoryObj<typeof TestWrapper>;

export const MeasuredData: Story = {
  args: {
    zoneKey: 'DK-DK2',
    co2intensity: 176.01,
    fossilFuelRatio: 0.1664,
    renewableRatio: 0.683,
    hasOutage: false,
  },
};

export const DisplayTitle: Story = {
  args: {
    zoneKey: 'US-TEX-ERCO',
    co2intensity: 176.01,
    fossilFuelRatio: 0.1664,
    renewableRatio: 0.683,
    hasOutage: false,
  },
};
export const TruncatedTitle: Story = {
  args: {
    zoneKey: 'US-CAL-CISO',
    co2intensity: 176.01,
    fossilFuelRatio: 0.1664,
    renewableRatio: 0.683,
    hasOutage: false,
  },
};
export const TruncatedAndEstimated: Story = {
  args: {
    zoneKey: 'US-CAL-CISO',
    co2intensity: 176.01,
    fossilFuelRatio: 0.1664,
    renewableRatio: 0.683,
    hasOutage: false,
    estimationMethod: 'TSA',
  },
};
