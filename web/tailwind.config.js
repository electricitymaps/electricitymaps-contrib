const defaultConfig = require('tailwindcss/defaultConfig');
const formsPlugin = require('@tailwindcss/forms');

/** @type {import('tailwindcss/types').Config} */
const config = {
  content: ['index.html', 'src/**/*.tsx'],
  theme: {
    extend: {
      fontSize: {
        '2xs': '.6rem',
      },
    },
    fontFamily: {
      sans: ['Inter', ...defaultConfig.theme.fontFamily.sans],
    },
  },
  experimental: { optimizeUniversalDefaults: true },
  plugins: [formsPlugin],
};
module.exports = config;
