/* eslint-disable unicorn/no-null */
import { Meta, StoryObj } from '@storybook/react';
import { zoneDetailMock } from 'stories/mockData';
import CarbonChartTooltip from './CarbonChartTooltip';

const meta: Meta<typeof CarbonChartTooltip> = {
  title: 'tooltips/CarbonChartTooltip',
  component: CarbonChartTooltip,
};

export default meta;

type Story = StoryObj<typeof CarbonChartTooltip>;

// Copying the mock data here to be able to make changes to it
const zoneDetail = { ...zoneDetailMock };

export const Primary: Story = {
  // More on args: https://storybook.js.org/docs/react/writing-stories/args
  args: {
    selectedLayerKey: 'carbonIntensity',
    zoneDetail: zoneDetail,
  },
};
