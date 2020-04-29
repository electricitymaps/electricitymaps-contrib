import React from 'react';
import { connect } from 'react-redux';

import MapCountryTooltip from '../components/tooltips/mapcountrytooltip';
import MapExchangeTooltip from '../components/tooltips/mapexchangetooltip';

import { MAP_COUNTRY_TOOLTIP_KEY } from '../helpers/constants';

const mapStateToProps = state => ({
  data: state.application.tooltipData,
  mode: state.application.tooltipDisplayMode,
  position: state.application.tooltipPosition,
});

const MapTooltips = ({ data, mode, position }) => (
  <React.Fragment>
    {/* TODO: Put this into Map component once it's been moved to React. */}
    {/* See https://github.com/tmrowco/electricitymap-contrib/issues/2309. */}
    {mode === MAP_COUNTRY_TOOLTIP_KEY && (
      <MapCountryTooltip position={position} zoneData={data} />
    )}
  </React.Fragment>
);

export default connect(mapStateToProps)(MapTooltips);
