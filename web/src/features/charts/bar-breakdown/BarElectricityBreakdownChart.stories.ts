import type { Meta, StoryObj } from '@storybook/react';
import BarElectricityBreakdownChart from './BarElectricityBreakdownChart';
import type { ZoneDetails } from 'types';
import { ExchangeDataType, ProductionDataType } from './utils';
import { zoneDetailMock } from 'stories/mockData';

const meta: Meta<typeof BarElectricityBreakdownChart> = {
  title: 'charts/BarElectricityBreakdownChart',
  component: BarElectricityBreakdownChart,
};

type Story = StoryObj<typeof BarElectricityBreakdownChart>;

// Copying the mock data here to be able to make changes to it
// const zoneDetail = {...zoneDetailMock};

const data: ZoneDetails = {
  hasData: true,
  stateAggregation: 'daily',
  zoneStates: {
    SOME_DATE: { ...zoneDetailMock },
  },
};

const productionData: ProductionDataType[] = [
  {
    storage: null,
    isStorage: false,
    production: null,
    capacity: 0,
    mode: 'nuclear',
    tCo2eqPerMin: 0,
  },
  {
    storage: null,
    isStorage: false,
    production: null,
    capacity: 0,
    mode: 'geothermal',
    tCo2eqPerMin: 0,
  },
  {
    storage: null,
    isStorage: false,
    production: 350,
    capacity: 700,
    mode: 'biomass',
    tCo2eqPerMin: 2.561_683_868_333_333,
  },
  {
    storage: null,
    isStorage: false,
    production: 0,
    capacity: 0,
    mode: 'coal',
    tCo2eqPerMin: 0,
  },
  {
    storage: null,
    isStorage: false,
    production: 2365,
    capacity: 5389,
    mode: 'wind',
    tCo2eqPerMin: 0.497_438_333_333_333_3,
  },
  {
    storage: null,
    isStorage: false,
    production: 17,
    capacity: 1616,
    mode: 'solar',
    tCo2eqPerMin: 0.007_253_333_333_333_333,
  },
  {
    isStorage: false,
    storage: -395,
    production: 1445,
    capacity: 4578,
    mode: 'hydro',
    tCo2eqPerMin: 0.257_691_666_666_666_65,
  },
  {
    isStorage: true,
    storage: -395,
    production: 1445,
    capacity: 3585,
    mode: 'hydro storage',
    tCo2eqPerMin: -0.898_247_560_136_053_7,
  },
  {
    isStorage: true,
    production: null,
    storage: null,
    capacity: null,
    mode: 'battery storage',
    tCo2eqPerMin: 0,
  },
  {
    isStorage: false,
    storage: null,
    production: 1930,
    capacity: 4520,
    mode: 'gas',
    tCo2eqPerMin: 15.829_517_778_833_331,
  },
  {
    isStorage: false,
    storage: null,
    production: null,
    capacity: 0,
    mode: 'oil',
    tCo2eqPerMin: 0,
  },
  {
    isStorage: false,
    storage: null,
    production: 29,
    capacity: null,
    mode: 'unknown',
    tCo2eqPerMin: 0.338_333_333_333_333_3,
  },
];

const exchangeData: ExchangeDataType[] = [
  {
    exchange: -934,
    zoneKey: 'ES',
    gCo2eqPerkWh: 187.32,
    tCo2eqPerMin: -2.915_948,
    exchangeCapacityRange: [-1000, 500],
  },
  {
    exchange: 200,
    zoneKey: 'FR',
    gCo2eqPerkWh: 999.32,
    tCo2eqPerMin: 45.915_948,
    exchangeCapacityRange: [-200, 500],
  },
];

export const IncludesStorage: Story = {
  // More on args: https://storybook.js.org/docs/react/writing-stories/args
  args: {
    //testId: 'none',
    data: data,
    productionData: productionData,
    exchangeData: exchangeData,
    onExchangeRowMouseOut: () => {},
    onExchangeRowMouseOver: () => {},
    onProductionRowMouseOut: () => {},
    onProductionRowMouseOver: () => {},
    width: 300,
    height: 300,
    isMobile: false,
  },
};

export default meta;
