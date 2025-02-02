import { MapTheme } from 'types';

const defaultCo2Scale = {
  steps: [0, 150, 600, 800, 1100, 1500],
  colors: ['#2AA364', '#F5EB4D', '#9E4229', '#381D02', '#381D02', '#000'],
};

const defaultPriceScale = {
  steps: [-100, -50, -20, 0, 20, 50, 75, 100, 125, 150, 800, 1000],
  colors: [
    '#0066cc', // deep blue for extreme negative
    '#3399ff', // medium blue
    '#66ccff', // light blue
    '#99ffff', // very light blue
    '#f5f5f5', // near white/neutral at 0
    '#ffe6cc', // very light orange
    '#ffcc99', // light orange
    '#ff9966', // medium orange
    '#ff6633', // dark orange
    '#ff3300', // bright red
    '#cc0000', // dark red
    '#990000', // very dark red
    '#660000', // deepest red
  ],
};

const colorblindCo2Scale = {
  steps: [0, 150, 600, 800, 1100, 1500],
  colors: ['#FFFFB0', '#E3BF66', '#BB833C', '#8B4D2B', '#4E241F', '#000'],
};

interface Colors {
  colorblindDark: MapTheme;
  dark: MapTheme;
  colorblindBright: MapTheme;
  bright: MapTheme;
}
export const colors: Colors = {
  colorblindDark: {
    co2Scale: colorblindCo2Scale,
    priceScale: defaultPriceScale,
    oceanColor: '#343D4C',
    strokeWidth: 0.15,
    strokeColor: '#6D6D6D',
    clickableFill: '#7A878D',
    stateBorderColor: '#d1d5db',
    nonClickableFill: '#7A878D',
  },
  dark: {
    co2Scale: defaultCo2Scale,
    priceScale: defaultPriceScale,
    oceanColor: '#343D4C',
    strokeWidth: 0.15,
    strokeColor: '#6D6D6D',
    stateBorderColor: '#d1d5db',
    clickableFill: '#7A878D',
    nonClickableFill: '#7A878D',
  },
  colorblindBright: {
    co2Scale: colorblindCo2Scale,
    priceScale: defaultPriceScale,
    oceanColor: '#FAFAFA',
    strokeWidth: 0.15,
    strokeColor: '#FAFAFA',
    stateBorderColor: '#d1d5db',
    clickableFill: '#D4D9DE',
    nonClickableFill: '#D4D9DE',
  },
  bright: {
    co2Scale: defaultCo2Scale,
    priceScale: defaultPriceScale,
    oceanColor: '#FAFAFA',
    strokeWidth: 0.15,
    strokeColor: '#FAFAFA',
    stateBorderColor: '#d1d5db',
    clickableFill: '#D4D9DE',
    nonClickableFill: '#D4D9DE',
  },
};
