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
      this.setZones(config.zones);
    }
  }

  setZones(zonesData) {
    const zones = d3.values(zonesData);
    const validatedAndSortedZones = this._sortAndValidateZones(zones);
    this.zones = this._saveZoneRankings(validatedAndSortedZones);
  }

  setCo2ColorScale(colorScale) {
    this.co2ColorScale = colorScale;
  }

  setClickHandler(clickHandler) {
    this.clickHandler = clickHandler;
  }

  filterZonesByQuery(query) {
    d3.select(this.selectorId).selectAll('a').each((zone, i, nodes) => {
      const listItem = d3.select(nodes[i]);
      if (this._zoneMatchesQuery(zone, query)) {
        listItem.style('display', 'inherit');
      } else {
        listItem.style('display', 'none');
      }
    });
  }

  clickSelectedItem() {
    // Item is selected when it is the only item visible in the list
    const visibleListItems = d3.select(this.selectorId).selectAll('a').nodes()
      .filter(node => node.style.display !== 'none');
    if (visibleListItems.length === 1) {
      visibleListItems[0].click();
    }
  }


  render() {
    this._createListItems();
    this._setItemAttributes();
    this._setItemClickHandlers();
  }

  _zoneMatchesQuery(zone, queryString) {
    const queries = queryString.split(' ');
    return queries.every(query =>
      translation.getFullZoneName(zone.countryCode)
        .toLowerCase()
        .indexOf(query.toLowerCase()) !== -1);
  }

  _sortAndValidateZones(zones) {
    return zones
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

  _saveZoneRankings(zones) {
    return zones.map((zone) => {
      const ret = Object.assign({}, zone);
      ret.ranking = zones.indexOf(zone) + 1;
      return ret;
    });
  }

  _createListItems() {
    this.selector = d3.select(this.selectorId)
      .selectAll('a')
      .data(this.zones);

    const itemLinks = this.selector.enter().append('a');

    itemLinks.append('div').attr('class', 'ranking');
    itemLinks.append('img').attr('class', 'flag');

    const nameDiv = itemLinks.append('div').attr('class', 'name');
    nameDiv.append('div').attr('class', 'zone-name');
    nameDiv.append('div').attr('class', 'country-name');

    itemLinks.append('div').attr('class', 'co2-intensity-tag');

    this.selector = itemLinks.merge(this.selector);
  }

  _setItemAttributes() {
    this._setItemRanks();
    this._setItemFlags();
    this._setItemNames();
    this._setItemCO2IntensityTag();
  }

  _setItemNames() {
    this.selector.select('.zone-name')
      .text(zone => translation.translate(`zoneShortName.${zone.countryCode}.zoneName`));

    this.selector.select('.country-name')
      .text(zone => translation.translate(`zoneShortName.${zone.countryCode}.countryName`));
  }

  _setItemRanks() {
    this.selector.select('div.ranking')
      .text(zone => zone.ranking);
  }

  _setItemFlags() {
    this.selector.select('.flag')
      .attr('src', zone => flags.flagUri(zone.countryCode, 32));
  }

  _setItemCO2IntensityTag() {
    this.selector.select('.co2-intensity-tag')
      .style('background-color', zone => (zone.co2intensity && this.co2ColorScale ? this.co2ColorScale(zone.co2intensity) : 'gray'));
  }

  _setItemClickHandlers() {
    this.selector.on('click', this.clickHandler);
  }
}
