import { Meta, StoryObj } from '@storybook/react';
import EmptyBarBreakdownChart from './EmptyBarBreakdownChart';

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
