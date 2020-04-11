import React from 'react';
import { connect } from 'react-redux';

import { __ } from '../../helpers/translation';
import { co2Sub } from '../../helpers/formatting';
import Tooltip from '../tooltip';

import { CarbonIntensity, ZoneName } from './common';

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
});

const MapExchangeTooltip = ({ colorBlindModeEnabled, exchangeData, position }) => {
  if (!exchangeData) return null;

  const isExporting = exchangeData.netFlow > 0;
  const netFlow = Math.abs(Math.round(exchangeData.netFlow));
  const zoneFrom = exchangeData.countryCodes[isExporting ? 0 : 1];
  const zoneTo = exchangeData.countryCodes[isExporting ? 1 : 0];

  return (
    <Tooltip id="exchange-tooltip" position={position}>
      {__('tooltips.crossborderexport')}:
      <br />
      <ZoneName zone={zoneFrom} /> → <ZoneName zone={zoneTo} />: <b>{netFlow}</b> MW
      <br />
      <br />
      <span dangerouslySetInnerHTML={{ __html: co2Sub(__('tooltips.carbonintensityexport')) }} />:
      <br />
      <CarbonIntensity
        colorBlindModeEnabled={colorBlindModeEnabled}
        intensity={exchangeData.co2intensity}
      />
    </Tooltip>
  );
};

export default connect(mapStateToProps)(MapExchangeTooltip);
