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
    this.zones = this._decorateZones(validatedAndSortedZones);
  }

  setCo2ColorScale(colorScale) {
    this.co2ColorScale = colorScale;
  }

  setClickHandler(clickHandler) {
    this.clickHandler = clickHandler;
  }

  filterZonesByQuery(query) {
    d3.select(this.selectorId).selectAll('.link-container').each((zone, i, nodes) => {
      const listItem = d3.select(nodes[i]);
      if (this._zoneMatchesQuery(zone, query)) {
        listItem.style('display', 'block');
      } else {
        listItem.style('display', 'none');
      }
    });
  }

  clickFirstItemIfVisibleListHasExactlyOneItem() {
    const visibleListItems = d3.selectAll(`${this.selectorId} .link-container`).nodes()
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

  _zoneMatchesQuery(zone, query) {
    return zone.countryName.toLowerCase().indexOf(query) !== -1
    || zone.zoneName.toLowerCase().indexOf(query) !== -1;
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

  _decorateZones(zones) {
    const zonesWithRankings = this._saveZoneRankings(zones);
    return this._splitZoneFullNamesIntoCountryAndZoneNames(zonesWithRankings);
  }

  _saveZoneRankings(zones) {
    return zones.map((zone) => {
      const ret = Object.assign({}, zone);
      ret.ranking = zones.indexOf(zone) + 1;
      return ret;
    });
  }

  _splitZoneFullNamesIntoCountryAndZoneNames(zones) {
    return zones.map((zone) => {
      const zoneFullName = translation.translate(`zoneShortName.${zone.countryCode}`) || zone.countryCode;
      const leftParanthesisIndex = zoneFullName.indexOf('(');
      const rightParanthesisIndex = zoneFullName.indexOf(')');
      const ret = Object.assign({}, zone);

      if (leftParanthesisIndex !== -1 && rightParanthesisIndex !== -1) {
        ret.countryName = zoneFullName.substring(0, leftParanthesisIndex - 1);
        ret.zoneName = zoneFullName
          .substring(leftParanthesisIndex + 1, rightParanthesisIndex);
      } else {
        ret.countryName = '';
        ret.zoneName = zoneFullName;
      }
      return ret;
    });
  }

  _createListItems() {
    this.selector = d3.select(this.selectorId)
      .selectAll('a')
      .data(this.zones);

    const linkContainers = this.selector.enter().append('div').attr('class', 'link-container');

    const enterA = linkContainers.append('a');

    enterA
      .append('div')
      .attr('class', 'ranking');
    enterA
      .append('img')
      .attr('class', 'flag');

    const nameDiv = enterA
      .append('div')
      .attr('class', 'name');
    nameDiv.append('div')
      .attr('class', 'zone-name');
    nameDiv.append('div')
      .attr('class', 'country-name');

    const emissionsDiv = enterA
      .append('div')
      .attr('class', 'emissions');

    emissionsDiv
      .append('div')
      .attr('class', 'emissions-value');

    emissionsDiv
      .append('div')
      .attr('class', 'emissions-unit');

    linkContainers.append('hr'); // border between items

    this.selector = linkContainers.merge(this.selector);
  }

  _setItemAttributes() {
    this._setItemRanks();
    this._setItemFlags();
    this._setItemNames();
    this._setItemEmissions();
  }

  _setItemNames() {
    this.selector.select('.zone-name')
      .text(zone => zone.zoneName);

    this.selector.select('.country-name')
      .text(zone => zone.countryName);
  }

  _setItemRanks() {
    this.selector.select('div.ranking')
      .text(zone => zone.ranking);
  }

  _setItemFlags() {
    this.selector.select('.flag')
      .attr('src', zone => flags.flagUri(zone.countryCode, 32));
  }

  _setItemEmissions() {
    this.selector.select('.emissions')
      .style('background-color', zone => (zone.co2intensity && this.co2ColorScale ? this.co2ColorScale(zone.co2intensity) : 'gray'));
    this.selector.select('.emissions .emissions-value')
      .text(zone => (zone.co2intensity ? Math.round(zone.co2intensity) : '-'));
    this.selector.select('.emissions .emissions-unit')
      .html('gCO<sub>2</sub>eq/kWh');
  }

  _setItemClickHandlers() {
    this.selector.on('click', this.clickHandler);
  }
}
