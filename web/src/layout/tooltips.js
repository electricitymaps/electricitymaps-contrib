import React from 'react';

import CountryPanelProductionTooltip from '../components/tooltips/countrypanelproductiontooltip';
import CountryPanelEmissionsTooltip from '../components/tooltips/countrypanelemissionstooltip';
import CountryPanelExchangeTooltip from '../components/tooltips/countrypanelexchangetooltip';
import LowCarbonInfoTooltip from '../components/tooltips/lowcarboninfotooltip';
import MapCountryTooltip from '../components/tooltips/mapcountrytooltip';
import MapExchangeTooltip from '../components/tooltips/mapexchangetooltip';
import PriceTooltip from '../components/tooltips/pricetooltip';

export default () => (
  <React.Fragment>
    <MapCountryTooltip />
    <MapExchangeTooltip />
    <PriceTooltip />
    <CountryPanelProductionTooltip />
    <CountryPanelEmissionsTooltip />
    <CountryPanelExchangeTooltip />
    <LowCarbonInfoTooltip />
  </React.Fragment>
);
