/// <reference types="vitest" />
import eslintPlugin from '@nabla/vite-plugin-eslint';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig(({ mode }) => ({
  optimizeDeps: {
    disabled: false,
  },
  define: {
    APP_VERSION: JSON.stringify(process.env.npm_package_version),
  },
  build: {
    sourcemap: true,
    commonjsOptions: {
      include: [],
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
      enabled: true,
      '100': true,
      reporter: ['text', 'lcov'],
      reportsDirectory: 'coverage',
    },
  },
  plugins: [
    tsconfigPaths(),
    react(),
    ...(mode !== 'test'
      ? [
          eslintPlugin(),
          VitePWA({
            registerType: 'autoUpdate',
            workbox: {
              maximumFileSizeToCacheInBytes: 3_500_000,
            },
            includeAssets: [
              'favicon.png',
              'robots.txt',
              'apple-touch-icon.png',
              'icons/*.svg',
              'fonts/*.woff2',
            ],
            manifest: {
              theme_color: '#BD34FE',
              icons: [
                {
                  src: '/android-chrome-192x192.png',
                  sizes: '192x192',
                  type: 'image/png',
                  purpose: 'any maskable',
                },
                {
                  src: '/android-chrome-512x512.png',
                  sizes: '512x512',
                  type: 'image/png',
                },
              ],
            },
          }),
        ]
      : []),
  ],
}));
