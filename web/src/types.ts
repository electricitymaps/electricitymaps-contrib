export interface IFruit {
  name: string;
  image: {
    author: {
      name: string;
      url: string;
    };
    color: string;
    url: string;
  };
  metadata: {
    name: string;
    value: string;
  }[];
}

export interface GridState {
  countries: Record<string, ZoneOverview[] | []>; // TODO: Can we change countries -> zones in app-backend?
}

export interface ZoneOverview {
  countryCode: string;
  co2intensity?: number;
  stateDatetime: string;
}

export interface ZoneDetail extends ZoneOverview {
  production: GenerationTypes;
  capacity: GenerationTypes;
}

export interface ZoneDetails {
  hasData: boolean;
  stateAggregation: 'daily' | 'hourly' | 'monthly' | 'yearly';
  zoneStates: ZoneDetail[];
}

export interface GenerationTypes {
  biomass?: number;
  coal?: number;
  gas?: number;
  geothermal?: number;
  hydro?: number;
  nuclear?: number;
  oil?: number;
  solar?: number;
  wind?: number;
  unknown?: number;
}

export interface StorageTypes {
  battery: number;
  hydro: number;
}

export enum TimeAverages {
  DAILY = 'daily',
  HOURLY = 'hourly',
  MONTHLY = 'monthly',
  YEARLY = 'yearly',
}
