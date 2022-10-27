import { CapacitorConfig } from '@capacitor/cli';

let config: CapacitorConfig;

const baseConfig: CapacitorConfig = {
  appId: 'com.tmrow.electricitymap',
  appName: 'Electricity Maps',
  webDir: '../webz/dist',
  bundledWebRuntime: false,
};



switch (process.env.NODE_ENV) {
  case 'qa':
    config = {
      ...baseConfig,
      server:{
        "url" : "http://localhost:5173/"
      }
    };
    break;
  default:
    config = baseConfig
    break;
}



export default config;
