import type { Duration } from 'date-fns';
import { ElectricityModeType } from 'types';

// The order here determines the order displayed
export enum TimeAverages {
  HOURLY = 'hourly',
  DAILY = 'daily',
  MONTHLY = 'monthly',
  YEARLY = 'yearly',
}

export enum ToggleOptions {
  ON = 'on',
  OFF = 'off',
}

export enum ThemeOptions {
  LIGHT = 'light',
  DARK = 'dark',
  SYSTEM = 'system',
}

export enum Mode {
  CONSUMPTION = 'consumption',
  PRODUCTION = 'production',
}

export enum SpatialAggregate {
  COUNTRY = 'country',
  ZONE = 'zone',
}

export enum LeftPanelToggleOptions {
  ELECTRICITY = 'electricity',
  EMISSIONS = 'emissions',
}

export enum TrackEvent {
  DATA_SOURCES_CLICKED = 'Data Sources Clicked',
}

// Production/imports-exports mode
export const modeColor: { [mode in ElectricityModeType]: string } = {
  solar: '#FFC700',
  wind: '#69D6F8',
  hydro: '#1878EA',
  'hydro storage': '#2B3CD8',
  'battery storage': '#1DA484',
  biomass: '#008043',
  geothermal: '#A73C15',
  nuclear: '#9D71F7',
  gas: '#AAA189',
  coal: '#545454',
  oil: '#584745',
  unknown: '#ACACAC',
};

export const modeOrder = [
  'nuclear',
  'geothermal',
  'biomass',
  'coal',
  'wind',
  'solar',
  'hydro',
  'hydro storage',
  'battery storage',
  'gas',
  'oil',
  'unknown',
] as const;

//A mapping between the TimeAverages enum and the corresponding Duration for the date-fns add/substract method
export const timeAxisMapping: Record<TimeAverages, keyof Duration> = {
  daily: 'days',
  hourly: 'hours',
  monthly: 'months',
  yearly: 'years',
};
