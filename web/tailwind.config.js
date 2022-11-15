const defaultConfig = require('tailwindcss/defaultConfig');
const formsPlugin = require('@tailwindcss/forms');

/** @type {import('tailwindcss/types').Config} */
const config = {
  content: ['index.html', 'src/**/*.tsx'],
  theme: {
    extend: {
      backgroundImage: {
        thumb: "url('/public/slider-thumb.svg')",
      },
      fontSize: {
        '2xs': '.6rem',
      },
      boxShadow: {
        '2xl': '0.1px 0.1px 5px rgba(0, 0, 0, 0.1)',
        '3xl': '0.1px 0.1px 6px rgba(0, 0, 0, 0.15);',
      },
      colors: {
        'green-900': '#135836',
      },
    },
    fontFamily: {
      sans: ['Inter', ...defaultConfig.theme.fontFamily.sans],
      poppins: ['Poppins', ...defaultConfig.theme.fontFamily.sans],
      inter: ['Inter', ...defaultConfig.theme.fontFamily.sans],
    },
    fontSize: {
      xs: '0.6rem',
      sm: '0.75rem',
      md: '0.8rem',
      base: '0.875rem',
      lg: '1.3rem',
      xl: '1.5rem',
    },
  },
  experimental: { optimizeUniversalDefaults: true },
  plugins: [formsPlugin],
};
module.exports = config;
