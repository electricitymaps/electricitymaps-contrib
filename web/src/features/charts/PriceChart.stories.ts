import type { Meta, StoryObj } from '@storybook/react';
import { TimeAverages } from '../../utils/constants';
import AreaGraph from './elements/AreaGraph';
import { getFills } from './hooks/usePriceChartData';
import { zoneDetailMock } from 'stories/mockData';

const meta: Meta<typeof AreaGraph> = {
  title: 'charts/PriceChart',
  component: AreaGraph,
};

export default meta;

type Story = StoryObj<typeof AreaGraph>;

const chartData = [
  {
    datetime: '2022-11-12T18:00:00.000Z',
    layerData: { price: 199.71 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-12T19:00:00.000Z',
    layerData: { price: 177.44 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-12T20:00:00.000Z',
    layerData: { price: 166.84 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-12T21:00:00.000Z',
    layerData: { price: 160.86 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-12T22:00:00.000Z',
    layerData: { price: 158.69 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-12T23:00:00.000Z',
    layerData: { price: 168.8 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T00:00:00.000Z',
    layerData: { price: 152.21 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T01:00:00.000Z',
    layerData: { price: 143 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T02:00:00.000Z',
    layerData: { price: 127 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T03:00:00.000Z',
    layerData: { price: 134.07 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T04:00:00.000Z',
    layerData: { price: 135.29 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T05:00:00.000Z',
    layerData: { price: 135.29 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T06:00:00.000Z',
    layerData: { price: 150.75 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T07:00:00.000Z',
    layerData: { price: 155.96 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T08:00:00.000Z',
    layerData: { price: 131.57 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T09:00:00.000Z',
    layerData: { price: 120.31 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T10:00:00.000Z',
    layerData: { price: 133 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T11:00:00.000Z',
    layerData: { price: 130.13 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T12:00:00.000Z',
    layerData: { price: 125 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T13:00:00.000Z',
    layerData: { price: 137.4 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T14:00:00.000Z',
    layerData: { price: 141.87 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T15:00:00.000Z',
    layerData: { price: 150.38 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T16:00:00.000Z',
    layerData: { price: 187.61 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T17:00:00.000Z',
    layerData: { price: 197.86 },
    meta: zoneDetailMock,
  },
  {
    datetime: '2022-11-13T18:00:00.000Z',
    layerData: { price: 165.12 },
    meta: zoneDetailMock,
  },
].map((d) => ({ ...d, datetime: new Date(d.datetime) }));

const negativePrices = [...chartData];

negativePrices[2] = {
  ...negativePrices[2],
  layerData: { price: -14 },
};
negativePrices[3] = {
  ...negativePrices[3],
  layerData: { price: -20 },
};
negativePrices[4] = {
  ...negativePrices[4],
  layerData: { price: -30 },
};

export const NegativePrices: Story = {
  // More on args: https://storybook.js.org/docs/react/writing-stories/args
  args: {
    testId: 'none',
    data: negativePrices,
    layerKeys: ['price'],
    layerStroke: undefined,
    layerFill: getFills(negativePrices).layerFill,
    markerFill: getFills(negativePrices).markerFill,
    selectedTimeAggregate: TimeAverages.HOURLY,
    valueAxisLabel: '€ / MWh',
    isMobile: false,
    height: '12em',
    datetimes: chartData.map((d) => d.datetime),
  },
};

const missingEntriesData = [...chartData];

missingEntriesData[4] = {
  ...missingEntriesData[4],
  layerData: { price: Number.NaN },
};

missingEntriesData[18] = {
  ...missingEntriesData[18],
  layerData: { price: Number.NaN },
};

missingEntriesData[19] = {
  ...missingEntriesData[19],
  layerData: { price: Number.NaN },
};

export const MissingEntries: Story = {
  // More on args: https://storybook.js.org/docs/react/writing-stories/args
  args: {
    testId: 'none',
    data: missingEntriesData,
    layerKeys: ['price'],
    layerStroke: undefined,
    layerFill: getFills(missingEntriesData).layerFill,
    markerFill: getFills(missingEntriesData).markerFill,
    selectedTimeAggregate: TimeAverages.HOURLY,
    valueAxisLabel: '€ / MWh',
    isMobile: false,
    height: '12em',
    datetimes: chartData.map((d) => d.datetime),
  },
};
