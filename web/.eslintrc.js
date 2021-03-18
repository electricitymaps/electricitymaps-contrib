/* eslint-env node */
module.exports = {
  parser: 'babel-eslint',
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:jest/recommended',
    'plugin:import/errors',
    'plugin:jsx-a11y/recommended',
  ],
  plugins: ['jest', 'react-hooks'],
  "globals": {
    "ELECTRICITYMAP_PUBLIC_TOKEN": "readonly",
    "VERSION": "readonly",
    "locale": "readonly",
    "codePush": "readonly",
    "device": "readonly",
    "cordova": "readonly",
    "resolvePath": "readonly",
    "universalLinks": "readonly",
    "InstallMode": "readonly",
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
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 2018,
    sourceType: 'module',
    createDefaultProgram: true,
  },
  overrides: [
    {
      files: ['*.spec.js', '*.spec.ts', '*.spec.tsx', '*.test.js', '*.test.ts', '*.test.tsx'],
      env: {
        'jest/globals': true,
      },
      rules: {
        'no-console': 'off',
      },
    },
  ],
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
    'no-unused-vars': [
      'error',
      { args: 'after-used', argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
    ],
    'no-use-before-define': ['error', { variables: true, functions: false, classes: true }],
    'prefer-const': 'error',
    'prefer-template': 'error',
    'react-hooks/exhaustive-deps': 'error',
    'react-hooks/rules-of-hooks': 'error',
    'react/jsx-filename-extension': ['error', { 'extensions': ['.js', '.jsx'] }],

    'react/self-closing-comp': 'error',
    'import/newline-after-import': 'error',
    'object-shorthand': 'error',

    // Rules we want to enable one day
    'no-console': 'warn',
    curly: 'warn',
    'no-nested-ternary': 'warn',
    'jsx-a11y/anchor-is-valid': 'warn',
    'jsx-a11y/click-events-have-key-events': 'warn',
    'jsx-a11y/no-noninteractive-element-interactions': 'warn',
    'jsx-a11y/no-static-element-interactions': 'warn',
    'max-len': ['warn', {'code': 120}],
    'no-underscore-dangle': 'warn',
    'react/jsx-one-expression-per-line': 'warn',

    // Rules that doesn't make sense for us:
    'jest/no-standalone-expect': 'off', // afterEach not covered
    'import/prefer-default-export': 'off',
    'import/named': 'off',
    'react/prop-types': 'off',
    'react/display-name': 'off',
    'import/order': 'off',
  },
};
