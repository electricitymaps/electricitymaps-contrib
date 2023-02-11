import type { Meta, StoryObj } from '@storybook/react';
import CarbonIntensitySquare from './CarbonIntensitySquare';

const meta: Meta<typeof CarbonIntensitySquare> = {
  title: 'Basics/CarbonIntensitySquare',
  component: CarbonIntensitySquare,
};
export default meta;
type Story = StoryObj<typeof CarbonIntensitySquare>;

export const Primary: Story = {
  args: {
    intensity: 234.123_123_123,
  },
};

export const WithLabel: Story = {
  args: {
    intensity: 234,
    withSubtext: true,
  },
};

export const InvalidNumber: Story = {
  args: {
    intensity: undefined,
    withSubtext: true,
  },
};
