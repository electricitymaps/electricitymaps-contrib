import type { Meta, StoryObj } from '@storybook/react';
import { TimeAverages } from 'utils/constants';

import TimeAverageToggle from './TimeAverageToggle';

const meta = {
  component: TimeAverageToggle,
  title: 'Toggles/TimeAverageToggle',
  args: {
    onToggleGroupClick: () => {},
  },
} satisfies Meta<typeof TimeAverageToggle>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Hourly: Story = {
  args: {
    timeAverage: TimeAverages.HOURLY,
  },
};

export const Daily: Story = {
  args: {
    timeAverage: TimeAverages.DAILY,
  },
};

export const Monthly: Story = {
  args: {
    timeAverage: TimeAverages.MONTHLY,
  },
};

export const Yearly: Story = {
  args: {
    timeAverage: TimeAverages.YEARLY,
  },
};
