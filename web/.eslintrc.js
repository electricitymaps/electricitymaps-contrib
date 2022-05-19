/* eslint-env node */
module.exports = {
  parser: '@babel/eslint-parser',
  extends: [
    'eslint:recommended',
    'plugin:you-dont-need-lodash-underscore/all',
    'plugin:react/recommended',
    'plugin:import/errors',
    'plugin:jsx-a11y/recommended',
    'plugin:cypress/recommended',
    'plugin:prettier/recommended',
  ],
  plugins: ['@babel', 'react-hooks'],
  globals: {
    ELECTRICITYMAP_PUBLIC_TOKEN: 'readonly',
    VERSION: 'readonly',
    codePush: 'readonly',
    device: 'readonly',
    cordova: 'readonly',
    resolvePath: 'readonly',
    universalLinks: 'readonly',
    InstallMode: 'readonly',
  },
  env: {
    es6: true,
    browser: true,
    node: true,
  },
  root: true,
  ignorePatterns: ['dist', 'build', '**/node_modules', '!.eslintrc.js', 'coverage'],
  settings: {
    react: {
      version: 'detect',
    },
    'import/resolver': {
      node: {
        extensions: ['.js', '.jsx', '.ts', '.tsx', '.json', '.ios.js', '.android.js'],
      },
    },
  },
  parserOptions: {
    requireConfigFile: false,
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 2018,
    sourceType: 'module',
    createDefaultProgram: true,
  },
  rules: {
    'prefer-destructuring': [
      'error',
      {
        array: false,
        object: true,
      },
    ],
    'dot-notation': 'error',
    'no-await-in-loop': 'error',
    'no-duplicate-imports': 'error',
    'no-implicit-coercion': 'error',
    'no-param-reassign': 'error',
    'no-unused-vars': ['error', { args: 'after-used', argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    'no-use-before-define': ['error', { variables: true, functions: false, classes: true }],
    'prefer-const': 'error',
    'prefer-template': 'error',
    'react/jsx-filename-extension': ['error'],

    'react/self-closing-comp': 'error',
    'import/newline-after-import': 'error',
    'object-shorthand': 'error',
    'react-hooks/exhaustive-deps': 'error',
    'react-hooks/rules-of-hooks': 'error',
    curly: 'error',
    'no-nested-ternary': 'error',
    'no-underscore-dangle': [
      'error',
      {
        allowAfterThis: true,
        allow: ['__', '__REDUX_DEVTOOLS_EXTENSION__'],
      },
    ],
    'no-console': ['error', { allow: ['error', 'warn'] }], // if .log is intended, use disable line.
    // Rules we want to enable soon!
    'jsx-a11y/anchor-is-valid': 'off',
    'jsx-a11y/click-events-have-key-events': 'off',
    'jsx-a11y/no-noninteractive-element-interactions': 'off',
    'jsx-a11y/no-static-element-interactions': 'off',

    // Rules that doesn't make sense for us:
    'import/prefer-default-export': 'off',
    'import/named': 'off',
    'react/prop-types': 'off',
    'react/display-name': 'off',
    'import/order': 'off',
  },
};
