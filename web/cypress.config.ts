import { defineConfig } from 'cypress';
import task from '@cypress/code-coverage/task';

export default defineConfig({
  fileServerFolder: 'dist',
  fixturesFolder: '../mockserver/public',
  projectId: '9z8tgk',
  video: false,
  watchForFileChanges: true,
  e2e: {
    baseUrl: 'http://127.0.0.1:5173/',
    specPattern: 'cypress/e2e/**/*.ts',
  },
  component: {
    devServer: {
      framework: 'react',
      bundler: 'vite',
    },
    setupNodeEvents(on, config) {
      task(on, config);
      return config;
    },
  },
  env: {
    codeCoverage: {
      exclude: 'cypress/**/*.*',
    },
  },
});
