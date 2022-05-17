// Snowpack Configuration File
// See all supported options: https://www.snowpack.dev/reference/configuration

/** @type {import("snowpack").SnowpackUserConfig } */
export default {
  mount: {
    public: { url: '/', static: true },
    src: '/dist',
    // Mounts parent config folder so we can import zones.json etc. in the src code
    '../config': '/config',
  },
  routes: [
    { match: 'routes', src: '.*', dest: '/index.html' },
  ],
  plugins: [
    '@snowpack/plugin-react-refresh',
    '@snowpack/plugin-sass',
  ],
  packageOptions: {
    polyfillNode: true,
  },
  devOptions: {
    hmr: true,
  },
  buildOptions: {
    /* ... */
  },
};
