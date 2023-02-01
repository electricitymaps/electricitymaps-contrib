/**
 * @type {Cypress.PluginConfig}
 */
export default (on: Cypress.PluginEvents, config: Cypress.PluginConfigOptions) => {
  // `on` is used to hook into various events Cypress emits
  // `config` is the resolved Cypress config
  on('before:browser:launch', (browser, launchOptions) => {
    if (browser.family === 'chromium' && browser.name !== 'electron') {
      // Cypress adds --disable-gpu flag by default on Linux
      // Get rid of it, as the map is rendered using WebGL, for which the GPU is required
      return {
        ...launchOptions,
        args: [
          ...launchOptions.args.filter((argument) => argument !== '--disable-gpu'),
          '--ignore-gpu-blacklist',
        ],
      };
    }
  });

  return config;
};
