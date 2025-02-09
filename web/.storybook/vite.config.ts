import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig(() => ({
  define: {
    APP_VERSION: JSON.stringify(process.env.npm_package_version),
  },
  server: { host: '127.0.0.1' },
  treeshake: 'smallest',
  plugins: [tsconfigPaths(), react()],
}));
