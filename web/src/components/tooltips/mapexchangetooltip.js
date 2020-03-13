import React from 'react';
import { connect } from 'react-redux';

import { MAP_EXCHANGE_TOOLTIP_KEY } from '../../helpers/constants';
import { __, getFullZoneName } from '../../helpers/translation';
import { getCo2Scale } from '../../helpers/scales';
import { co2Sub } from '../../helpers/formatting';
import { flagUri } from '../../helpers/flags';

import Tooltip from '../tooltip';

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  // TODO: Should probably rename tooltipZoneData -> tooltipData
  exchangeData: state.application.tooltipZoneData,
  visible: state.application.tooltipDisplayMode === MAP_EXCHANGE_TOOLTIP_KEY,
});

const MapExchangeTooltip = ({ colorBlindModeEnabled, exchangeData, visible }) => {
  if (!visible) return null;

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const { co2intensity } = exchangeData;

  const isExporting = exchangeData.netFlow > 0;
  const zoneFrom = exchangeData.countryCodes[isExporting ? 0 : 1];
  const zoneTo = exchangeData.countryCodes[isExporting ? 1 : 0];

  return (
    <Tooltip id="exchange-tooltip">
      {__('tooltips.crossborderexport')}
      :
      <br />
      <img className="from flag" alt="" src={flagUri(zoneFrom)} />
      {' '}
      <span id="from">{getFullZoneName(zoneFrom)}</span>
       → 
      <img className="to flag" alt="" src={flagUri(zoneTo)} />
      {' '}
      <span id="to">{getFullZoneName(zoneTo)}</span>
      : 
      <span id="flow" style={{ fontWeight: 'bold' }}>
        {Math.abs(Math.round(exchangeData.netFlow))}
      </span>
      MW
      <br />
      <br />
      <span dangerouslySetInnerHTML={{ __html: co2Sub(__('tooltips.carbonintensityexport')) }} />
      :
      <br />
      <div className="emission-rect" style={{ backgroundColor: co2intensity ? co2ColorScale(co2intensity) : 'gray' }} />
      {' '}
      <span className="country-emission-intensity emission-intensity">
        {Math.round(co2intensity) || '?'}
      </span>
      gCO
      <span className="sub">2</span>
      eq/kWh
    </Tooltip>
  );
};

export default connect(mapStateToProps)(MapExchangeTooltip);
