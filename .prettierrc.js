module.exports = {
  semi: true,
  singleQuote: true,
  trailingComma: 'es5',
  printWidth: 90,
  overrides: [
    {
      files: '*.md',
      options: {
        printWidth: 90,
      },
    },
    {
      files: 'config/*.yaml',
      options: {
        printWidth: 120,
      },
    },
  ],
};
