import React from 'react';

import { useTranslation } from '../../helpers/translation';
import { formatPower } from '../../helpers/formatting';
import Tooltip from '../tooltip';

import { CarbonIntensity, ZoneName } from './common';

const MapExchangeTooltip = ({ exchangeData, position, onClose }) => {
  const { __ } = useTranslation();
  if (!exchangeData) {
    return null;
  }

  const isExporting = exchangeData.netFlow > 0;
  const netFlow = Math.abs(Math.round(exchangeData.netFlow));
  const zoneFrom = exchangeData.countryCodes[isExporting ? 0 : 1];
  const zoneTo = exchangeData.countryCodes[isExporting ? 1 : 0];

  return (
    <Tooltip id="exchange-tooltip" position={position} onClose={onClose}>
      {__('tooltips.crossborderexport')}:
      <br />
      <ZoneName zone={zoneFrom} /> → <ZoneName zone={zoneTo} />: <b>{formatPower(netFlow)}</b>
      <br />
      <br />
      {__('tooltips.carbonintensityexport')}:
      <br />
      <CarbonIntensity intensity={exchangeData.co2intensity} />
    </Tooltip>
  );
};

export default MapExchangeTooltip;
