module.exports = {
  root: true,
  overrides: [
    {
      files: ['*.ts?(x)'],
      parser: '@typescript-eslint/parser',
      parserOptions: {
        project: './tsconfig.json',
        tsconfigRootDir: __dirname,
      },
      env: {
        'cypress/globals': true,
      },
      plugins: ['cypress'],
      extends: [
        'eslint:recommended',
        'plugin:import/warnings',
        'plugin:import/errors',
        'plugin:import/typescript',
        'plugin:@typescript-eslint/recommended',
        'plugin:@typescript-eslint/recommended-requiring-type-checking',
        'airbnb-typescript/base',
        'plugin:unicorn/recommended',
        'prettier',
      ],
      rules: {
        'import/namespace': 'off',
        'import/no-extraneous-dependencies': 'off',
        '@typescript-eslint/no-unused-expressions': 'off',
        'no-void': 'off',

        'cypress/no-assigning-return-values': 'error',
        'cypress/no-unnecessary-waiting': 'error',
        'cypress/no-async-tests': 'error',
        'cypress/no-force': 'error',
        'cypress/assertion-before-screenshot': 'error',
        'cypress/require-data-selectors': 'error',
        'cypress/no-pause': 'error',
      },
    },
  ],
};
