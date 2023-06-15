export enum TimeAverages {
  DAILY = 'daily',
  HOURLY = 'hourly',
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

// Production/imports-exports mode
export const modeColor: { [key: string]: any } = {
  solar: '#f27406',
  wind: '#74cdb9',
  hydro: '#2772b2',
  'hydro storage': '#0052cc',
  battery: 'lightgray',
  'battery storage': '#b76bcf',
  biomass: '#166a57',
  geothermal: 'yellow',
  nuclear: '#AEB800',
  gas: '#bb2f51',
  coal: '#ac8c35',
  oil: '#867d66',
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
