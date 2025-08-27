import { CapacitorConfig } from '@capacitor/cli';

let config: CapacitorConfig;

const baseConfig: CapacitorConfig = {
  appId: 'com.tmrow.electricitymap',
  appName: 'Electricity Maps',
  webDir: '../web/dist',
  bundledWebRuntime: false,
  ios: {
    scheme: 'Electricity Maps',
  },
  android: {
    adjustMarginsForEdgeToEdge: 'force',
  },
  plugins: {
    StatusBar: {
      overlaysWebView: false,
      style: 'DEFAULT',
    },
  },
};

switch (process.env.NODE_ENV) {
  case 'dev':
    console.log('Serving app with dev config pointed to localhost:5173');
    config = {
      ...baseConfig,
      server: {
        // Optionally use 'http://localhost:5173?remote=true'
        url: 'http://localhost:5173',
        cleartext: true,
      },
    };
    break;
  default:
    config = baseConfig;
    break;
}

export default config;
