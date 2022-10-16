const { defineConfig } = require('cypress');

module.exports = defineConfig({
  projectId: '9z8tgk',
  video: false,
  fixturesFolder: '../mockserver/public',
  e2e: {
    setupNodeEvents(on, config) {
      return require('./cypress/plugins/index.js')(on, config);
    },
    baseUrl: 'http://localhost:8080',
    specPattern: 'cypress/e2e/**/*.{js,jsx,ts,tsx}',
  },
});
