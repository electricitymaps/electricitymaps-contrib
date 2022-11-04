import { defineConfig } from 'cypress';

export default defineConfig({
  fileServerFolder: 'dist',
  fixturesFolder: '../mockserver/public',
  projectId: '9z8tgk',
  video: false,
  e2e: {
    baseUrl: 'http://localhost:5173/',
    specPattern: 'cypress/e2e/**/*.ts',
  },
  component: {
    devServer: {
      framework: 'react',
      bundler: 'vite',
    },
  },
});
