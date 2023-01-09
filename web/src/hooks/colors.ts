const defaultCo2Scale = {
  steps: [0, 150, 600, 750, 800],
  colors: ['#2AA364', '#F5EB4D', '#9E4229', '#381D02', '#381D02'],
};

const colorblindCo2Scale = {
  steps: [0, 200, 400, 600, 800],
  colors: ['#FFFFB0', '#E0B040', '#A06030', '#602020', '#000010'],
};

interface ThemeColor {
  co2Scale: {
    steps: number[];
    colors: string[];
  };
  oceanColor: string;
  strokeWidth: number;
  strokeColor: string;
  clickableFill: string;
  nonClickableFill: string;
}

interface Colors {
  colorblindDark: ThemeColor;
  dark: ThemeColor;
  colorblindBright: ThemeColor;
  bright: ThemeColor;
}
export const colors: Colors = {
  colorblindDark: {
    co2Scale: colorblindCo2Scale,
    oceanColor: '#33414A',
    strokeWidth: 0.3,
    strokeColor: '#6D6D6D',
    clickableFill: '#7A878D',
    nonClickableFill: '#7A878D',
  },
  dark: {
    co2Scale: defaultCo2Scale,
    oceanColor: '#33414A',
    strokeWidth: 0.3,
    strokeColor: '#6D6D6D',
    clickableFill: '#7A878D',
    nonClickableFill: '#7A878D',
  },
  colorblindBright: {
    co2Scale: colorblindCo2Scale,
    oceanColor: '#FAFAFA',
    strokeWidth: 0.3,
    strokeColor: '#FAFAFA',
    clickableFill: '#D4D9DE',
    nonClickableFill: '#D4D9DE',
  },
  bright: {
    co2Scale: defaultCo2Scale,
    oceanColor: '#FAFAFA',
    strokeWidth: 0.3,
    strokeColor: '#FAFAFA',
    clickableFill: '#D4D9DE',
    nonClickableFill: '#D4D9DE',
  },
};
