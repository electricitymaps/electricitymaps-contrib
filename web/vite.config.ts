/// <reference types="vitest" />
import eslintPlugin from '@nabla/vite-plugin-eslint';
import { sentryVitePlugin, SentryVitePluginOptions } from '@sentry/vite-plugin';
import react from '@vitejs/plugin-react-swc';
import browserslistToEsbuild from 'browserslist-to-esbuild';
import { defineConfig } from 'vite';
import { ManifestOptions, VitePWA } from 'vite-plugin-pwa';
import tsconfigPaths from 'vite-tsconfig-paths';

const manualChunkMap = {
  '@sentry': 'sentry',
  '@radix-ui': 'radix',
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
    name: `app@${process.env.npm_package_version}`,
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
  scope_extensions: [{ origin: 'app.electricitymaps.com' }],
  launch_handler: {
    client_mode: 'auto',
  },
  description:
    'Electricity Maps is a live visualization of where your electricity comes from and how much CO2 was emitted to produce it.',
  theme_color: '#000000',
  icons: [
    {
      src: '/icons/icon.svg',
      sizes: '512x512 any',
      type: 'image/svg+xml',
      purpose: 'any',
    },
    {
      src: '/icons/icon-maskable.svg',
      sizes: '512x512 any',
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
  screenshots: [
    {
      src: '/images/screenshots/desktop/1.png',
      sizes: '1440x1024',
      type: 'image/png',
      form_factor: 'wide',
    },
    {
      src: '/images/screenshots/desktop/2.png',
      sizes: '1440x1024',
      type: 'image/png',
      form_factor: 'wide',
    },
    {
      src: '/images/screenshots/desktop/3.png',
      sizes: '1440x1024',
      type: 'image/png',
      form_factor: 'wide',
    },
    {
      src: '/images/screenshots/desktop/4.png',
      sizes: '1440x1024',
      type: 'image/png',
      form_factor: 'wide',
    },
    {
      src: '/images/screenshots/mobile/1.png',
      sizes: '786x1704',
      type: 'image/png',
      form_factor: 'narrow',
    },
    {
      src: '/images/screenshots/mobile/2.png',
      sizes: '786x1704',
      type: 'image/png',
      form_factor: 'narrow',
    },
    {
      src: '/images/screenshots/mobile/3.png',
      sizes: '786x1704',
      type: 'image/png',
      form_factor: 'narrow',
    },
    {
      src: '/images/screenshots/mobile/4.png',
      sizes: '786x1704',
      type: 'image/png',
      form_factor: 'narrow',
    },
    {
      src: '/images/screenshots/mobile/5.png',
      sizes: '786x1704',
      type: 'image/png',
      form_factor: 'narrow',
    },
  ],
};

export default defineConfig(({ mode }) => ({
  define: {
    APP_VERSION: JSON.stringify(process.env.npm_package_version),
  },
  server: { host: '127.0.0.1' },
  build: {
    target: browserslistToEsbuild(),
    sourcemap: true,
    rollupOptions: {
      output: {
        experimentalMinChunkSize: 3500,
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
    react(
      mode === 'production'
        ? {}
        : {
            devTarget: 'es2022',
            plugins: [
              ['@swc-jotai/react-refresh', {}],
              ['@swc-jotai/debug-label', {}],
            ],
          }
    ),
    ...(mode === 'test'
      ? []
      : [
          eslintPlugin(),
          VitePWA({
            registerType: 'autoUpdate',
            workbox: {
              skipWaiting: true,
              clientsClaim: true,
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
