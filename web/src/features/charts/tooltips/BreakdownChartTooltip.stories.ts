import { Meta, StoryObj } from '@storybook/react';
import { TimeRange } from 'utils/constants';

import { BreakdownChartTooltipContent } from './BreakdownChartTooltip';

const meta: Meta<typeof BreakdownChartTooltipContent> = {
  title: 'tooltips/BreakdownChartTooltipContent',
  component: BreakdownChartTooltipContent,
};

export default meta;

type Story = StoryObj<typeof BreakdownChartTooltipContent>;

export const Example: Story = {
  // More on args: https://storybook.js.org/docs/react/writing-stories/args
  args: {
    datetime: new Date('2022-11-28T07:00:00.000Z'),
    usage: 599,
    timeRange: TimeRange.H72,
    capacity: 500,
    co2Intensity: 130,
    co2IntensitySource: 'IPCC 2014; EU-ETS, ENTSO-E 2021',
    displayByEmissions: false,
    emissions: 100_000_000,
    totalElectricity: 1100,
    totalEmissions: 1_200_000_000,
    selectedLayerKey: 'nuclear',
    zoneKey: 'DK-DK1',
  },
};

export const WithoutCapacity: Story = {
  // More on args: https://storybook.js.org/docs/react/writing-stories/args
  args: {
    datetime: new Date('2022-11-28T07:00:00.000Z'),
    usage: 599,
    timeRange: TimeRange.H72,
    capacity: undefined,
    co2Intensity: 130,
    co2IntensitySource: 'IPCC 2014; EU-ETS, ENTSO-E 2021',
    displayByEmissions: false,
    emissions: 100_000_000,
    totalElectricity: 1100,
    totalEmissions: 1_200_000_000,
    selectedLayerKey: 'nuclear',
    zoneKey: 'DK-DK1',
  },
};

export const isStoring: Story = {
  // More on args: https://storybook.js.org/docs/react/writing-stories/args
  args: {
    datetime: new Date('2022-11-28T07:00:00.000Z'),
    usage: 80,
    timeRange: TimeRange.H72,
    capacity: 700,
    co2Intensity: 130,
    co2IntensitySource: 'IPCC 2014; EU-ETS, ENTSO-E 2021',
    displayByEmissions: false,
    emissions: 100_000_000,
    totalElectricity: 1100,
    totalEmissions: 1_200_000_000,
    selectedLayerKey: 'hydro storage',
    zoneKey: 'PL',
    storage: 60,
    production: 0,
    isExchange: false,
    isExport: true,
  },
};

export const IsDischarging: Story = {
  // More on args: https://storybook.js.org/docs/react/writing-stories/args
  args: {
    datetime: new Date('2022-11-28T07:00:00.000Z'),
    usage: 80,
    timeRange: TimeRange.H72,
    capacity: 700,
    co2Intensity: 130,
    co2IntensitySource: 'IPCC 2014; EU-ETS, ENTSO-E 2021',
    displayByEmissions: false,
    emissions: 100_000_000,
    totalElectricity: 1100,
    totalEmissions: 1_200_000_000,
    selectedLayerKey: 'battery storage',
    zoneKey: 'PL',
    storage: 0,
    production: 80,
  },
};

export const LongSource: Story = {
  // More on args: https://storybook.js.org/docs/react/writing-stories/args
  args: {
    datetime: new Date('2022-11-28T07:00:00.000Z'),
    usage: 80,
    timeRange: TimeRange.H72,
    capacity: 700,
    co2Intensity: 130,
    co2IntensitySource:
      'IPCC 2014; EU-ETS, ENTSO-E 2021 IPCC 2014; EU-ETS, ENTSO-E 2021 IPCC 2014; EU-ETS, ENTSO-E 2021 IPCC 2014; EU-ETS, ENTSO-E 2021',
    displayByEmissions: false,
    emissions: 100_000_000,
    totalElectricity: 1100,
    totalEmissions: 1_200_000_000,
    selectedLayerKey: 'battery storage',
    zoneKey: 'PL',
    storage: 0,
    production: 80,
  },
};
export const Exporting: Story = {
  // More on args: https://storybook.js.org/docs/react/writing-stories/args
  args: {
    datetime: new Date('2022-11-28T07:00:00.000Z'),
    usage: 80,
    timeRange: TimeRange.H72,
    capacity: 700,
    co2Intensity: 450,
    co2IntensitySource:
      'IPCC 2014; EU-ETS, ENTSO-E 2021 IPCC 2014; EU-ETS, ENTSO-E 2021 IPCC 2014; EU-ETS, ENTSO-E 2021 IPCC 2014; EU-ETS, ENTSO-E 2021',
    displayByEmissions: false,
    emissions: 100_000_000,
    totalElectricity: 1100,
    totalEmissions: 1_200_000_000,
    isExport: true,
    selectedLayerKey: 'DE',
    zoneKey: 'DK-DK1',
    storage: 0,
    production: 80,
    isExchange: true,
  },
};
