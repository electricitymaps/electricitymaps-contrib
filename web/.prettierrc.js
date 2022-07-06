const config = require('../.prettierrc.js');

module.exports = {
  // Ensures the web config is the same as the global config.
  ...config,
};
