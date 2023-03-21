const defaultConfig = require('tailwindcss/defaultConfig');
const formsPlugin = require('@tailwindcss/forms');
const radix = require('tailwindcss-radix');
const typography = require('@tailwindcss/typography');

/** @type {import('tailwindcss/types').Config} */
const config = {
  content: ['index.html', 'src/**/*.tsx'],
  darkMode: 'class',
  theme: {
    extend: {
      animation: {
        'slide-down': 'slide-down 0.3s cubic-bezier(0.87, 0, 0.13, 1)',
        'slide-up': 'slide-up 0.3s cubic-bezier(0.87, 0, 0.13, 1)',
      },
      keyframes: {
        'slide-down': {
          '0%': { height: '0' },
          '100%': { height: 'var(--radix-accordion-content-height)' },
        },
        'slide-up': {
          '0%': { height: 'var(--radix-accordion-content-height)' },
          '100%': { height: '0' },
        },
      },
      boxShadow: {
        '2xl': '0.1px 0.1px 5px rgba(0, 0, 0, 0.1)',
        '3xl': '0.1px 0.1px 6px rgba(0, 0, 0, 0.15);',
      },
      colors: {
        'brand-green': '#135836',
        'brand-yellow': '#E9B73B',
        'brand-brown': '#702214',
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
      '2xl': '3rem',
    },
  },
  plugins: [formsPlugin, typography, radix()],
};
module.exports = config;
