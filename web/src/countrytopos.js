const world = require('./world.json');

var exports = module.exports = {};

exports.addCountryTopos = (countries) => {
  Object.entries(world).forEach((entry) => {
    const [k, v] = entry;
    countries[k] = v;
  });

  return countries;
};
