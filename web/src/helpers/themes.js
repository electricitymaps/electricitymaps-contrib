export const shared = {
  fontFamily: "'Euclid Triangle', 'Open Sans', sans-serif",
  strokeWidth: 0.3,
};

export const co2Scales = {
  default: {
    steps: [0, 150, 600, 750, 800],
    colors: ['#2AA364', '#F5EB4D', '#9E4229', '#381D02', '#381D02'],
  },
  colorblind: {
    steps: [0, 200, 400, 600, 800],
    colors: ['#FFFFB0', '#E0B040', '#A06030', '#602020', '#000010'],
  },
};

export const themes = {
  dark: {
    name: 'dark',
    oceanColor: '#33414A',
    background: '#33414A',
    lightBackground: '#495d69',
    shadowColor: 'rgba(0, 0, 0, 0.3)',
    shadowColorHovered: 'rgba(0, 0, 0, 0.5)',
    text: '#FAFAFA',
    textFaded: '#FAFAFABB',
    strokeColor: '#6D6D6D',
    clickableFill: '#7A878D',
    nonClickableFill: '#7A878D',
  },

  bright: {
    name: 'bright',
    oceanColor: '#FAFAFA',
    background: '#FAFAFA',
    lightBackground: '#FFFFFF',
    shadowColor: 'rgba(0, 0, 0, 0.1)',
    shadowColorHovered: 'rgba(0, 0, 0, 0.2)',
    text: '#000000',
    textFaded: '#000000BB',
    strokeColor: '#FAFAFA',
    clickableFill: '#D4D9DE',
    nonClickableFill: '#D4D9DE',
  },
};
