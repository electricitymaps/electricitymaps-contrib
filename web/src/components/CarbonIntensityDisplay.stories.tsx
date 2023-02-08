import type { Meta, StoryObj } from '@storybook/react';

import React from 'react';
import { HiMagnifyingGlass } from 'react-icons/hi2';
import { CarbonIntensityDisplay } from './CarbonIntensityDisplay';

const meta: Meta<typeof CarbonIntensityDisplay> = {
  title: 'Basics/CarbonIntensityDisplay',
  component: CarbonIntensityDisplay,
};
export default meta;
type Story = StoryObj<typeof CarbonIntensityDisplay>;

export const Primary: Story = {
  args: {
    co2Intensity: 234.123_123_123,
  },
};

export const WithSquare: Story = {
  args: {
    co2Intensity: 234.123_123_123,
    withSquare: true,
  },
};

export const InvalidNumber: Story = {
  args: {
    co2Intensity: undefined,
    withSquare: true,
  },
};
