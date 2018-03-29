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
    this.clickHandler = config.clickHandler;
    if (config.zones) {
      this._sortAndValidateZones(config.zones);
    }
  }

  setZones(zones) {
    this._sortAndValidateZones(zones);
  }

  setCo2ColorScale(colorScale) {
    this.co2ColorScale = colorScale;
  }

  setClickHandler(clickHandler) {
    this.clickHandler = clickHandler;
  }

  filterZonesByQuery(query) {
    d3.select(this.selectorId).selectAll('a').each((obj, i, nodes) => {
      const zoneName = (obj.shortname || obj.countryCode).toLowerCase();
      const listItem = d3.select(nodes[i]);

      if (zoneName.indexOf(query) !== -1) {
        listItem.style('display', 'inherit');
      } else {
        listItem.style('display', 'none');
      }
    });
  }

  render() {
    this._createListItems();
    this._setItemAttributes();
    this._setItemClickHandlers();
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
    this.selector = d3.select(this.selectorId)
      .selectAll('a')
      .data(this.zones);
    const enterA = this.selector.enter().append('a');
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

    this.selector = enterA.merge(this.selector);
  }

  _setItemAttributes() {
    this._setItemTexts();
    this._setItemBackgroundColors();
    this._setItemFlags();
  }

  _setItemTexts() {
    this.selector.select('span.name')
      .text(zone => ` ${translation.translate(`zoneShortName.${zone.countryCode}`) || zone.countryCode} `);
  }

  _setItemBackgroundColors() {
    this.selector.select('div.emission-rect')
      .style('background-color', zone => (zone.co2intensity && this.co2ColorScale ? this.co2ColorScale(zone.co2intensity) : 'gray'));
  }

  _setItemFlags() {
    this.selector.select('.flag')
      .attr('src', zone => flags.flagUri(zone.countryCode, 16));
  }

  _setItemClickHandlers() {
    this.selector.on('click', this.clickHandler);
  }
}
