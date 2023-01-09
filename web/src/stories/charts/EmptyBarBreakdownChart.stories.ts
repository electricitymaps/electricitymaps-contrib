import { Meta, StoryObj } from '@storybook/react';
import BarBreakdownEmissionsChart from 'features/charts/bar-breakdown/BarBreakdownEmissionsChart';
import EmptyBarBreakdownChart from 'features/charts/bar-breakdown/EmptyBarBreakdownChart';

const meta: Meta<typeof EmptyBarBreakdownChart> = {
  title: 'charts/EmptyBarBreakdownChart',
  component: EmptyBarBreakdownChart,
};

type Story = StoryObj<typeof EmptyBarBreakdownChart>;

export const Primary: Story = {
  args: {
    width: 500,
    height: 500,
    overLayText: 'No data',
  },
};

export default meta;
