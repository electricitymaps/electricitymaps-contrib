import type { Meta, StoryObj } from '@storybook/react';
import { TimeRange } from 'utils/constants';

import TimeRangeToggle from './TimeRangeToggle';

const meta = {
  component: TimeRangeToggle,
  title: 'Toggles/TimeRangeToggle',
  args: {
    onToggleGroupClick: () => {},
  },
} satisfies Meta<typeof TimeRangeToggle>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Hourly: Story = {
  args: {
    timeRange: TimeRange.H24,
  },
};

export const Hourly72: Story = {
  args: {
    timeRange: TimeRange.H72,
  },
};

export const Daily: Story = {
  args: {
    timeRange: TimeRange.D30,
  },
};

export const Monthly: Story = {
  args: {
    timeRange: TimeRange.M12,
  },
};

export const Yearly: Story = {
  args: {
    timeRange: TimeRange.ALL,
  },
};
