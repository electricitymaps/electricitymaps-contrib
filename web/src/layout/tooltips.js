import React from 'react';

import CountryPanelEmissionsTooltip from '../components/tooltips/countrypanelemissionstooltip';
import LowCarbonInfoTooltip from '../components/tooltips/lowcarboninfotooltip';
import MapCountryTooltip from '../components/tooltips/mapcountrytooltip';
import MapExchangeTooltip from '../components/tooltips/mapexchangetooltip';

export default () => (
  <React.Fragment>
    <MapCountryTooltip />
    <MapExchangeTooltip />
    <CountryPanelEmissionsTooltip />
    <LowCarbonInfoTooltip />
  </React.Fragment>
);
