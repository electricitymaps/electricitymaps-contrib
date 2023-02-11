import { CapacitorConfig } from '@capacitor/cli';

let config: CapacitorConfig;

const baseConfig: CapacitorConfig = {
  appId: 'com.tmrow.electricitymap',
  appName: 'Electricity Maps',
  webDir: '../web/dist',
  bundledWebRuntime: false,
};

switch (process.env.NODE_ENV) {
  case 'dev':
    console.log('Serving app with dev config pointed to localhost:5173');
    config = {
      ...baseConfig,
      server: {
        url: 'use address from pnpm dev --host',
        cleartext: true,
      },
    };
    break;
  default:
    config = baseConfig;
    break;
}

export default config;
