/// <reference types="vitest" />
import eslintPlugin from '@nabla/vite-plugin-eslint';
import { sentryVitePlugin, SentryVitePluginOptions } from '@sentry/vite-plugin';
import react from '@vitejs/plugin-react';
import jotaiDebugLabel from 'jotai/babel/plugin-debug-label';
import jotaiReactRefresh from 'jotai/babel/plugin-react-refresh';
import { defineConfig } from 'vite';
import { ManifestOptions, VitePWA } from 'vite-plugin-pwa';
import tsconfigPaths from 'vite-tsconfig-paths';

const manualChunkMap = {
  '@sentry': 'sentry',
  '@radix-ui': 'radix',
  recharts: 'recharts',
  'world.json': 'world',
  'usa_states.json': 'config',
  'zones.json': 'config',
  'exchanges.json': 'config',
  'excluded_aggregated_exchanges.json': 'config',
};

const sentryPluginOptions: SentryVitePluginOptions = {
  org: 'electricitymaps',
  project: 'app-web',

  // Auth tokens can be obtained from https://sentry.io/settings/account/api/auth-tokens/
  // and needs the `project:releases` and `org:read` scopes
  authToken: process.env.SENTRY_AUTH_TOKEN,

  release: {
    // Optionally uncomment the line below to override automatic release name detection
    name: process.env.npm_package_version,
  },
  bundleSizeOptimizations: {
    excludeDebugStatements: true,
    excludePerformanceMonitoring: true,
    excludeReplayIframe: true,
    excludeReplayShadowDom: true,
    excludeReplayWorker: true,
  },
};

const PWAManifest: Partial<ManifestOptions> = {
  name: 'Electricity Maps',
  short_name: 'Electricity Maps',
  start_url: '/',
  display: 'standalone',
  background_color: '#ffffff',
  lang: 'en',
  scope: '/',
  description:
    'Electricity Maps is a live visualization of where your electricity comes from and how much CO2 was emitted to produce it.',
  theme_color: '#000000',
  icons: [
    {
      src: '/icons/icon.svg',
      sizes: 'any',
      type: 'image/svg+xml',
    },
    {
      src: '/icons/icon-maskable.svg',
      sizes: 'any',
      type: 'image/svg+xml',
      purpose: 'maskable',
    },
  ],
  iarc_rating_id: '194a8347-3f9e-4525-9e04-9969d2db0f56',
  prefer_related_applications: true,
  related_applications: [
    {
      platform: 'play',
      url: 'https://play.google.com/store/apps/details?id=com.tmrow.electricitymap',
      id: 'com.tmrow.electricitymap',
    },
    {
      platform: 'itunes',
      url: 'https://apps.apple.com/app/electricitymap/id1224594248',
      id: '1224594248',
    },
  ],
  id: 'com.tmrow.electricitymap',
  categories: ['education'],
  display_override: ['standalone', 'window-controls-overlay'],
  orientation: 'any',
};

export default defineConfig(({ mode }) => ({
  define: {
    APP_VERSION: JSON.stringify(process.env.npm_package_version),
  },
  server: { host: '127.0.0.1' },
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          for (const [searchString, value] of Object.entries(manualChunkMap)) {
            if (id.includes(searchString)) {
              return value;
            }
          }
        },
      },
    },
  },
  treeshake: 'smallest',
  test: {
    css: false,
    include: ['{src,geo}/**/*.test.{ts,tsx}', 'scripts/*.test.{ts,tsx}'],
    globals: true,
    globalSetup: 'testSetup.ts',
    environment: 'jsdom',
    setupFiles: 'src/testing/setupTests.ts',
    clearMocks: true,
    coverage: {
      provider: 'istanbul',
      enabled: false,
      100: true,
      reporter: ['text', 'lcov'],
      reportsDirectory: 'coverage',
    },
  },
  plugins: [
    tsconfigPaths(),
    react({
      babel: {
        plugins: [jotaiDebugLabel, jotaiReactRefresh],
      },
    }),
    ...(mode === 'test'
      ? []
      : [
          eslintPlugin(),
          VitePWA({
            registerType: 'prompt',
            workbox: {
              maximumFileSizeToCacheInBytes: 3_500_000,
              runtimeCaching: [
                {
                  urlPattern: ({ url }) => url.pathname.startsWith('/images/'),
                  handler: 'CacheFirst',
                  options: {
                    cacheName: 'images',
                    cacheableResponse: {
                      statuses: [200],
                    },
                  },
                },
                {
                  urlPattern: ({ url }) => url.pathname.startsWith('/icons/'),
                  handler: 'CacheFirst',
                  options: {
                    cacheName: 'icons',
                    cacheableResponse: {
                      statuses: [200],
                    },
                  },
                },
              ],
            },
            includeAssets: ['robots.txt', 'fonts/**/*.{woff2, pbf}'],
            manifest: PWAManifest,
          }),
          // Used to upload sourcemaps to Sentry
          process.env.SENTRY_AUTH_TOKEN && sentryVitePlugin(sentryPluginOptions),
        ]),
  ],
}));
