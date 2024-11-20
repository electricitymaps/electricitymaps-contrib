import type { Meta, StoryObj } from '@storybook/react';
import { zoneStateMock } from 'stories/mockData';

import { TooltipInner } from './MapTooltip';

interface StoryStateZoneData {
  zoneKey: string;
  ci: number;
  fr: number;
  rr: number;
  e?: boolean | null;
  o?: boolean | null;
}

function TestWrapper({ zoneKey, ci, fr, rr, e, o }: StoryStateZoneData) {
  return (
    <div className="pointer-events-none relative w-[361px] rounded-2xl border border-neutral-200 bg-white text-sm shadow-lg dark:border-gray-700 dark:bg-gray-900 ">
      <div>
        <TooltipInner
          zoneData={{
            ...zoneStateMock,
            c: {
              ci,
              fr,
              rr,
            },
            e,
            o,
          }}
          zoneId={zoneKey}
        />
      </div>
    </div>
  );
}

const meta: Meta<typeof TestWrapper> = {
  title: 'tooltips/MapTooltip',
  component: TestWrapper,
};

export default meta;
type Story = StoryObj<typeof TestWrapper>;

export const MeasuredData: Story = {
  args: {
    zoneKey: 'DK-DK2',
    ci: 176.01,
    fr: 0.1664,
    rr: 0.683,
    o: false,
    e: false,
  },
};

export const DisplayTitle: Story = {
  args: {
    zoneKey: 'US-TEX-ERCO',
    ci: 176.01,
    fr: 0.1664,
    rr: 0.683,
    o: false,
    e: false,
  },
};
export const TruncatedTitle: Story = {
  args: {
    zoneKey: 'US-CAL-CISO',
    ci: 176.01,
    fr: 0.1664,
    rr: 0.683,
    o: false,
    e: false,
  },
};
export const TruncatedAndEstimated: Story = {
  args: {
    zoneKey: 'US-CAL-CISO',
    ci: 176.01,
    fr: 0.1664,
    rr: 0.683,
    o: false,
    e: true,
  },
};
