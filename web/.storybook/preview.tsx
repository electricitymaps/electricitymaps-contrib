import { withThemeByClassName } from '@storybook/addon-themes';
import React, { Suspense, useEffect } from 'react';
import { I18nextProvider } from 'react-i18next';

import '../src/index.css';
import i18n from '../src/translation/i18n';
import { languageNames } from '../src/translation/locales';

export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' },
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
};

const withI18next = (Story, context) => {
  const { locale } = context.globals;

  // When the locale global changes
  // Set the new locale in i18n
  useEffect(() => {
    i18n.changeLanguage(locale);
  }, [locale]);

  return (
    <Suspense fallback={<div>loading translations...</div>}>
      <I18nextProvider i18n={i18n}>
        <Story />
      </I18nextProvider>
    </Suspense>
  );
};

export const decorators = [
  withThemeByClassName({
    themes: {
      light: '',
      dark: 'dark',
    },
    defaultTheme: 'light',
  }),
  withI18next,
];

export const globalTypes = {
  locale: {
    name: 'Locale',
    description: 'Internationalization locale',
    toolbar: {
      icon: 'globe',
      items: Object.entries(languageNames).map((language) => ({
        value: language[0],
        title: language[1],
      })),
      defaultValue: 'en',
      showName: true,
    },
  },
};

export const tags = ['autodocs'];
