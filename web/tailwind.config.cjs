const defaultTheme = require('tailwindcss/defaultTheme');
const defaultConfig = require('tailwindcss/defaultConfig');
const formsPlugin = require('@tailwindcss/forms');
const radix = require('tailwindcss-radix');
const typography = require('@tailwindcss/typography');
const colors = require('tailwindcss/colors');

/** @type {import('tailwindcss/types').Config} */
const config = {
  content: ['index.html', 'src/**/*.tsx'],
  darkMode: 'class',
  theme: {
    extend: {
      typography: {
        DEFAULT: {
          css: {
            '--tw-prose-links': colors.emerald[800],
            '--tw-prose-invert-links': colors.emerald[500],
          },
        },
      },
      spacing: {
        15: '3.75rem',
      },
      padding: {
        safe: 'env(safe-area-inset-top)',
      },
      screens: {
        xs: '475px',
      },
      fontSize: {
        xxs: '0.625rem', // 10px
      },
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
        'brand-green-dark': '#41866B',
        'brand-yellow': '#E9B73B',
        'brand-brown': '#702214',
        'price-light': '#18214F',
        'price-dark': '#848EC0',
        secondary: {
          DEFAULT: colors.neutral[600],
          dark: colors.gray[300],
        },
        'info-base': {
          DEFAULT: colors.blue[700],
          dark: colors.blue[300],
        },
        'info-subtle': {
          DEFAULT: colors.blue[200],
          dark: colors.blue[800],
        },
        'info-muted': {
          DEFAULT: colors.blue[50],
          dark: colors.blue[950],
        },
        success: {
          DEFAULT: colors.emerald[800],
          dark: colors.emerald[500],
        },
        warning: {
          DEFAULT: colors.amber[700],
          dark: colors.amber[500],
        },
        danger: {
          DEFAULT: colors.red[700],
          dark: colors.red[400],
        },
        sunken: {
          DEFAULT: colors.neutral[100],
          dark: colors.neutral[800],
        },
        stroke: {
          DEFAULT: colors.neutral[200],
          dark: colors.neutral[800],
        },
      },
      minWidth: { 18: '4.5rem' },
    },
    fontFamily: {
      sans: ['Inter', ...defaultConfig.theme.fontFamily.sans],
      poppins: ['Poppins', ...defaultConfig.theme.fontFamily.sans],
      inter: ['Inter', ...defaultConfig.theme.fontFamily.sans],
    },
  },
  plugins: [formsPlugin, typography, radix()],
};
module.exports = config;
