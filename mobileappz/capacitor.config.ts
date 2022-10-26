import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.tmrow.electricitymap',
  appName: 'Electricity Maps',
  webDir: '../webz/dist',
  bundledWebRuntime: false,
  server:{
    "url" : "http://localhost:5173/"
  }
};

export default config;
