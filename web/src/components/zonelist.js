import dispatchApplication from '../helpers/dispatcher';

const translation = require('../helpers/translation');
const flags = require('../helpers/flags');

const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-collection'),
  require('d3-selection'),
);

export default class ZoneList {
  constructor(selectorId, argConfig) {
    this.selectorId = selectorId;

    const config = argConfig || {};
    this.co2ColorScale = config.co2ColorScale;
  }

  render(zones) {
    this._sortAndValidateZones(zones);
    this._createListItems();
    this._setItemAttributes();
    this._setItemClickHandlers();
  }

  setCo2ColorScale(colorScale) {
    this.co2ColorScale = colorScale;
  }

  _sortAndValidateZones(zones) {
    this.zones = d3.values(zones)
      .filter(d => d.co2intensity)
      .sort((x, y) => {
        if (!x.co2intensity && !x.countryCode) {
          return d3.ascending(
            x.shortname || x.countryCode,
            y.shortname || y.countryCode,
          );
        }
        return d3.ascending(
          x.co2intensity || Infinity,
          y.co2intensity || Infinity,
        );
      });
  }

  _createListItems() {
    const selector = d3.select(this.selectorId) // '.country-picker-container p'
      .selectAll('a')
      .data(this.zones);

    const enterA = selector.enter().append('a');
    enterA
      .append('div')
      .attr('class', 'emission-rect');
    enterA
      .append('span')
      .attr('class', 'name');
    enterA
      .append('img')
      .attr('class', 'flag');
    enterA
      .append('span')
      .attr('class', 'rank');

    this.selector = enterA.merge(selector);
  }

  _setItemAttributes() {
    this._setItemTexts();
    this._setItemBackgroundColors();
    this._setItemFlags();
  }

  _setItemTexts() {
    this.selector.select('span.name')
      .text(d => ` ${translation.translate(`zoneShortName.${d.countryCode}`) || d.countryCode} `);
  }

  _setItemBackgroundColors() {
    this.selector.select('div.emission-rect')
      .style('background-color', d => (d.co2intensity && this.co2ColorScale ? this.co2ColorScale(d.co2intensity) : 'gray'));
  }

  _setItemFlags() {
    this.selector.select('.flag')
      .attr('src', d => flags.flagUri(d.countryCode, 16));
  }

  _setItemClickHandlers() {
    this.selector.on('click', (d) => {
      dispatchApplication('showPageState', 'country');
      dispatchApplication('selectedZoneName', d.countryCode);
    });
  }
}
