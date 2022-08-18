module.exports = {
  semi: true,
  overrides: [
    {
      files: ['*.mts', '*.cts', '*.ts'],
      options: {
        parser: 'typescript',
      },
    },
  ],
  singleQuote: true,
  trailingComma: 'es5',
  printWidth: 120,
  overrides: [
    {
      files: '*.md',
      options: {
        printWidth: 80,
      },
    },
  ],
};
