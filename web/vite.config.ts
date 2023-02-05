/// <reference types="vitest" />
import eslintPlugin from '@nabla/vite-plugin-eslint';
import sentryVitePlugin from '@sentry/vite-plugin';
import react from '@vitejs/plugin-react';
import jotaiDebugLabel from 'jotai/babel/plugin-debug-label';
import jotaiReactRefresh from 'jotai/babel/plugin-react-refresh';
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';
import tsconfigPaths from 'vite-tsconfig-paths';

const manualChunkMap = {
  '@sentry': 'sentry',
  '@radix-ui': 'radix',
  'country-flag-icons': 'flags',
  recharts: 'recharts',
  'world.json': 'world',
  'zones.json': 'config',
  'exchanges.json': 'config',
  'excludedAggregatedExchanges.json': 'config',
};

export default defineConfig(({ mode }) => ({
  define: {
    APP_VERSION: JSON.stringify(process.env.npm_package_version),
  },
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
  test: {
    css: false,
    include: ['src/**/*.test.{ts,tsx}'],
    globals: true,
    environment: 'jsdom',
    setupFiles: 'src/testing/setupTests.ts',
    clearMocks: true,
    coverage: {
      provider: 'istanbul',
      enabled: false,
      '100': true,
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
    ...(mode !== 'test'
      ? [
          eslintPlugin(),
          // Temporarily disabled to ensure we can more easily rollback
          VitePWA({
            registerType: 'autoUpdate',
            workbox: {
              maximumFileSizeToCacheInBytes: 3_500_000,
            },
            includeAssets: [
              'icons/*.{svg,png}',
              'robots.txt',
              // Consider if we should also add subdirectories below
              'images/*.{svg,png,webp}',
              'images/arrows/*.webp',
              'fonts/*.woff2',
              'locales/*.json',
            ],
            manifest: {
              name: 'Electricity Maps',
              short_name: 'ElectricityMaps',
              description:
                'The Electricity Maps app is a live visualization of where your electricity comes from and how much CO2 was emitted to produce it.',
              theme_color: '#000',
              start_url: '/',
              display: 'standalone',
              prefer_related_applications: true,
              iarc_rating_id: '194a8347-3f9e-4525-9e04-9969d2db0f56',
              icons: [
                {
                  src: 'icons/windows11/SmallTile.scale-100.png',
                  sizes: '71x71',
                },
                {
                  src: 'icons/windows11/SmallTile.scale-125.png',
                  sizes: '89x89',
                },
                {
                  src: 'icons/windows11/SmallTile.scale-150.png',
                  sizes: '107x107',
                },
                {
                  src: 'icons/windows11/SmallTile.scale-200.png',
                  sizes: '142x142',
                },
                {
                  src: 'icons/windows11/SmallTile.scale-400.png',
                  sizes: '284x284',
                },
                {
                  src: 'icons/windows11/Square150x150Logo.scale-100.png',
                  sizes: '150x150',
                },
                {
                  src: 'icons/windows11/Square150x150Logo.scale-125.png',
                  sizes: '188x188',
                },
                {
                  src: 'icons/windows11/Square150x150Logo.scale-150.png',
                  sizes: '225x225',
                },
                {
                  src: 'icons/windows11/Square150x150Logo.scale-200.png',
                  sizes: '300x300',
                },
                {
                  src: 'icons/windows11/Square150x150Logo.scale-400.png',
                  sizes: '600x600',
                },
                {
                  src: 'icons/windows11/Wide310x150Logo.scale-100.png',
                  sizes: '310x150',
                },
                {
                  src: 'icons/windows11/Wide310x150Logo.scale-125.png',
                  sizes: '388x188',
                },
                {
                  src: 'icons/windows11/Wide310x150Logo.scale-150.png',
                  sizes: '465x225',
                },
                {
                  src: 'icons/windows11/Wide310x150Logo.scale-200.png',
                  sizes: '620x300',
                },
                {
                  src: 'icons/windows11/Wide310x150Logo.scale-400.png',
                  sizes: '1240x600',
                },
                {
                  src: 'icons/windows11/LargeTile.scale-100.png',
                  sizes: '310x310',
                },
                {
                  src: 'icons/windows11/LargeTile.scale-125.png',
                  sizes: '388x388',
                },
                {
                  src: 'icons/windows11/LargeTile.scale-150.png',
                  sizes: '465x465',
                },
                {
                  src: 'icons/windows11/LargeTile.scale-200.png',
                  sizes: '620x620',
                },
                {
                  src: 'icons/windows11/LargeTile.scale-400.png',
                  sizes: '1240x1240',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.scale-100.png',
                  sizes: '44x44',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.scale-125.png',
                  sizes: '55x55',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.scale-150.png',
                  sizes: '66x66',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.scale-200.png',
                  sizes: '88x88',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.scale-400.png',
                  sizes: '176x176',
                },
                {
                  src: 'icons/windows11/StoreLogo.scale-100.png',
                  sizes: '50x50',
                },
                {
                  src: 'icons/windows11/StoreLogo.scale-125.png',
                  sizes: '63x63',
                },
                {
                  src: 'icons/windows11/StoreLogo.scale-150.png',
                  sizes: '75x75',
                },
                {
                  src: 'icons/windows11/StoreLogo.scale-200.png',
                  sizes: '100x100',
                },
                {
                  src: 'icons/windows11/StoreLogo.scale-400.png',
                  sizes: '200x200',
                },
                {
                  src: 'icons/windows11/SplashScreen.scale-100.png',
                  sizes: '620x300',
                },
                {
                  src: 'icons/windows11/SplashScreen.scale-125.png',
                  sizes: '775x375',
                },
                {
                  src: 'icons/windows11/SplashScreen.scale-150.png',
                  sizes: '930x450',
                },
                {
                  src: 'icons/windows11/SplashScreen.scale-200.png',
                  sizes: '1240x600',
                },
                {
                  src: 'icons/windows11/SplashScreen.scale-400.png',
                  sizes: '2480x1200',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-16.png',
                  sizes: '16x16',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-20.png',
                  sizes: '20x20',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-24.png',
                  sizes: '24x24',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-30.png',
                  sizes: '30x30',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-32.png',
                  sizes: '32x32',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-36.png',
                  sizes: '36x36',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-40.png',
                  sizes: '40x40',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-44.png',
                  sizes: '44x44',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-48.png',
                  sizes: '48x48',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-60.png',
                  sizes: '60x60',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-64.png',
                  sizes: '64x64',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-72.png',
                  sizes: '72x72',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-80.png',
                  sizes: '80x80',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-96.png',
                  sizes: '96x96',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.targetsize-256.png',
                  sizes: '256x256',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-16.png',
                  sizes: '16x16',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-20.png',
                  sizes: '20x20',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-24.png',
                  sizes: '24x24',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-30.png',
                  sizes: '30x30',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-32.png',
                  sizes: '32x32',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-36.png',
                  sizes: '36x36',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-40.png',
                  sizes: '40x40',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-44.png',
                  sizes: '44x44',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-48.png',
                  sizes: '48x48',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-60.png',
                  sizes: '60x60',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-64.png',
                  sizes: '64x64',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-72.png',
                  sizes: '72x72',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-80.png',
                  sizes: '80x80',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-96.png',
                  sizes: '96x96',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-unplated_targetsize-256.png',
                  sizes: '256x256',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-16.png',
                  sizes: '16x16',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-20.png',
                  sizes: '20x20',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-24.png',
                  sizes: '24x24',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-30.png',
                  sizes: '30x30',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-32.png',
                  sizes: '32x32',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-36.png',
                  sizes: '36x36',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-40.png',
                  sizes: '40x40',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-44.png',
                  sizes: '44x44',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-48.png',
                  sizes: '48x48',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-60.png',
                  sizes: '60x60',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-64.png',
                  sizes: '64x64',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-72.png',
                  sizes: '72x72',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-80.png',
                  sizes: '80x80',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-96.png',
                  sizes: '96x96',
                },
                {
                  src: 'icons/windows11/Square44x44Logo.altform-lightunplated_targetsize-256.png',
                  sizes: '256x256',
                },
                {
                  src: 'icons/android/android-launchericon-512-512.png',
                  sizes: '512x512',
                },
                {
                  src: 'icons/android/android-launchericon-192-192.png',
                  sizes: '192x192',
                },
                {
                  src: 'icons/android/android-launchericon-144-144.png',
                  sizes: '144x144',
                },
                {
                  src: 'icons/android/android-launchericon-96-96.png',
                  sizes: '96x96',
                },
                {
                  src: 'icons/android/android-launchericon-72-72.png',
                  sizes: '72x72',
                },
                {
                  src: 'icons/android/android-launchericon-48-48.png',
                  sizes: '48x48',
                },
                {
                  src: 'icons/ios/16.png',
                  sizes: '16x16',
                },
                {
                  src: 'icons/ios/20.png',
                  sizes: '20x20',
                },
                {
                  src: 'icons/ios/29.png',
                  sizes: '29x29',
                },
                {
                  src: 'icons/ios/32.png',
                  sizes: '32x32',
                },
                {
                  src: 'icons/ios/40.png',
                  sizes: '40x40',
                },
                {
                  src: 'icons/ios/50.png',
                  sizes: '50x50',
                },
                {
                  src: 'icons/ios/57.png',
                  sizes: '57x57',
                },
                {
                  src: 'icons/ios/58.png',
                  sizes: '58x58',
                },
                {
                  src: 'icons/ios/60.png',
                  sizes: '60x60',
                },
                {
                  src: 'icons/ios/64.png',
                  sizes: '64x64',
                },
                {
                  src: 'icons/ios/72.png',
                  sizes: '72x72',
                },
                {
                  src: 'icons/ios/76.png',
                  sizes: '76x76',
                },
                {
                  src: 'icons/ios/80.png',
                  sizes: '80x80',
                },
                {
                  src: 'icons/ios/87.png',
                  sizes: '87x87',
                },
                {
                  src: 'icons/ios/100.png',
                  sizes: '100x100',
                },
                {
                  src: 'icons/ios/114.png',
                  sizes: '114x114',
                },
                {
                  src: 'icons/ios/120.png',
                  sizes: '120x120',
                },
                {
                  src: 'icons/ios/128.png',
                  sizes: '128x128',
                },
                {
                  src: 'icons/ios/144.png',
                  sizes: '144x144',
                },
                {
                  src: 'icons/ios/152.png',
                  sizes: '152x152',
                },
                {
                  src: 'icons/ios/167.png',
                  sizes: '167x167',
                },
                {
                  src: 'icons/ios/180.png',
                  sizes: '180x180',
                },
                {
                  src: 'icons/ios/192.png',
                  sizes: '192x192',
                },
                {
                  src: 'icons/ios/256.png',
                  sizes: '256x256',
                },
                {
                  src: 'icons/ios/512.png',
                  sizes: '512x512',
                },
                {
                  src: 'icons/ios/1024.png',
                  sizes: '1024x1024',
                },
              ],
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
            },
          }),
          // Used to upload sourcemaps to Sentry
          process.env.SENTRY_AUTH_TOKEN &&
            sentryVitePlugin({
              org: 'electricitymaps',
              project: 'app-web',

              // Specify the directory containing build artifacts
              include: './dist',

              // Auth tokens can be obtained from https://sentry.io/settings/account/api/auth-tokens/
              // and needs the `project:releases` and `org:read` scopes
              authToken: process.env.SENTRY_AUTH_TOKEN,

              // Optionally uncomment the line below to override automatic release name detection
              release: process.env.npm_package_version,
            }),
        ]
      : []),
  ],
}));
