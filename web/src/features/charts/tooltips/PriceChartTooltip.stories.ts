import { Meta, StoryObj } from '@storybook/react';
import { zoneDetailMock } from 'stories/mockData';

import PriceChartTooltip from './PriceChartTooltip';

const meta: Meta<typeof PriceChartTooltip> = {
  title: 'tooltips/PriceChartTooltip',
  component: PriceChartTooltip,
};

export default meta;

type Story = StoryObj<typeof PriceChartTooltip>;

// Copying the mock data here to be able to make changes to it
const zoneDetail = { ...zoneDetailMock };

export const Primary: Story = {
  // More on args: https://storybook.js.org/docs/react/writing-stories/args
  args: {
    selectedLayerKey: 'carbonIntensity',
    zoneDetail: zoneDetail,
  },
};
