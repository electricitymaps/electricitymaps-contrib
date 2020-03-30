import React from 'react';

import LowCarbonInfoTooltip from '../components/tooltips/lowcarboninfotooltip';
import MapCountryTooltip from '../components/tooltips/mapcountrytooltip';
import MapExchangeTooltip from '../components/tooltips/mapexchangetooltip';

export default () => (
  <React.Fragment>
    <MapCountryTooltip />
    <MapExchangeTooltip />
    <LowCarbonInfoTooltip />
  </React.Fragment>
);
