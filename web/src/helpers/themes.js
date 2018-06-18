const themes = {
  dark: {
    co2Scale: {
      steps: [0, 150, 600, 750],
      oldsteps: [0, 250, 700, 800],
      colors: ['#2AA364', '#F5EB4D', '#9E293E', '#1B0E01'],
      oldcolors: ['#13663B', '#FFF668', '#BA102F', '#1B0E01'],
    },
    oceanColor: '#0D263A',
    strokeWidth: 0.3,
    strokeColor: '#33414A',
    clickableFill: '#54626B',
    nonClickableFill: '#54626B',
  },
  bright: {
    co2Scale: {
      steps: [0, 150, 600, 750],
      oldsteps: [0, 250, 700, 800],
      colors: ['#2AA364', '#F5EB4D', '#9E293E', '#1B0E01'],
      oldcolors: ['#13663B', '#F5EB4D', '#BA102F', '#1B0E01'],
    },
    oceanColor: '#FAFAFA',
    strokeWidth: 0.3,
    strokeColor: '#FAFAFA',
    clickableFill: '#D4D9DE',
    nonClickableFill: '#D4D9DE',
  },
};

module.exports = {
  themes,
};
