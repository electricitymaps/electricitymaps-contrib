import { ElectricityModeType } from 'types';

export const LABEL_MAX_WIDTH = 118;
export const TEXT_ADJUST_Y = 11;
export const ROW_HEIGHT = 13;
export const PADDING_Y = 7;
export const PADDING_X = 5;
export const RECT_OPACITY = 0.8;
export const X_AXIS_HEIGHT = 15;
export const DEFAULT_FLAG_SIZE = 16;
export const SCALE_TICKS = 4;

export const iconHeight: { [mode in ElectricityModeType]: string } = {
  solar: '10',
  wind: '8',
  hydro: '7',
  'hydro storage': '8',
  'battery storage': '6',
  biomass: '9',
  geothermal: '8',
  nuclear: '8',
  gas: '9',
  coal: '9',
  oil: '9',
  unknown: '8',
};
