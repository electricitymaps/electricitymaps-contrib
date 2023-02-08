import type { Meta, StoryObj } from '@storybook/react';

import { HiMagnifyingGlass } from 'react-icons/hi2';
import { CircularGauge } from './CircularGauge';

const meta: Meta<typeof CircularGauge> = {
  title: 'Basics/CircularGauge',
  component: CircularGauge,
};

export default meta;
type Story = StoryObj<typeof CircularGauge>;

export const Default: Story = {
  argTypes: {
    ratio: {
      control: { type: 'number', min: 0, max: 1, step: 0.1 },
    },
  },
  args: {
    ratio: 0.5,
    name: 'Renewable',
  },
};

export const WithTooltip: Story = {
  argTypes: {
    ratio: {
      control: { type: 'number', min: 0, max: 1, step: 0.1 },
    },
  },
  args: {
    tooltipContent: (
      <div>
        Hello <strong>friend</strong>
      </div>
    ),
    ratio: 0.5,
    name: 'Renewable',
  },
};
