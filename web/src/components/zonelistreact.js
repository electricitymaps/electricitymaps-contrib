const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-collection'),
  require('d3-scale'),
  require('d3-selection'),
);

import React from 'react';
import { connect } from 'react-redux';

const { themes } = require('../helpers/themes');
const translation = require('../helpers/translation');
const flags = require('../helpers/flags');

function getCo2Scale(colorBlindModeEnabled) {
  if (colorBlindModeEnabled) {
    return d3.scaleLinear()
      .domain(themes.colorblindScale.steps)
      .range(themes.colorblindScale.colors)
      .clamp(true);
  }

  return d3.scaleLinear()
    .domain(themes.co2Scale.steps)
    .range(themes.co2Scale.colors)
    .clamp(true);
}

function withZoneRankings(zones) {
  return zones.map((zone) => {
    const ret = Object.assign({}, zone);
    ret.ranking = zones.indexOf(zone) + 1;
    return ret;
  });
}

function getCo2IntensityAccessor(electricityMixMode) {
  return d => (electricityMixMode === 'consumption'
    ? d.co2intensity
    : d.co2intensityProduction);
}

function sortAndValidateZones(zones, accessor) {
  return zones
    .filter(accessor)
    .sort((x, y) => {
      if (!x.co2intensity && !x.countryCode) {
        return d3.ascending(
          x.shortname || x.countryCode,
          y.shortname || y.countryCode,
        );
      }
      return d3.ascending(
        accessor(x) || Infinity,
        accessor(y) || Infinity,
      );
    });
}

function processZones(zonesData, accessor) {
  const zones = d3.values(zonesData);
  const validatedAndSortedZones = sortAndValidateZones(zones, accessor);
  return withZoneRankings(validatedAndSortedZones);
}

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  electricityMixMode: state.application.electricityMixMode,
  gridZones: state.data.grid.zones,
});

const ZoneList = ({ colorBlindModeEnabled, electricityMixMode, gridZones }) => {
  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const co2IntensityAccessor = getCo2IntensityAccessor(electricityMixMode);
  const zones = processZones(gridZones, co2IntensityAccessor);

  return (
    <div className="zone-list-react">
      {zones.map(zone => (
        <a key={zone.shortname}>
          <div className="ranking">{zone.ranking}</div>
          <img className="flag" src={flags.flagUri(zone.countryCode, 32)} />
          <div className="name">
            <div className="zone-name">{translation.translate(`zoneShortName.${zone.countryCode}.zoneName`)}</div>
            <div className="country-name">{translation.translate(`zoneShortName.${zone.countryCode}.countryName`)}</div>
          </div>
          <div
            className="co2-intensity-tag"
            style={{
              backgroundColor: co2IntensityAccessor(zone) && co2ColorScale
                ? co2ColorScale(co2IntensityAccessor(zone))
                : 'gray'
            }}
          />
        </a>
      ))}
    </div>
  );
}

export default connect(mapStateToProps)(ZoneList);
