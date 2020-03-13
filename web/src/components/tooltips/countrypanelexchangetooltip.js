import React, { useRef } from 'react';
import { connect } from 'react-redux';
import { isFinite } from 'lodash';

import { __, getFullZoneName } from '../../helpers/translation';
import { co2Sub, formatCo2, formatPower } from '../../helpers/formatting';
import { getCo2Scale } from '../../helpers/scales';
import { flagUri } from '../../helpers/flags';
import { modifyDOM } from '../../helpers/dom';
import { getSelectedZoneExchangeKeys } from '../../selectors';
import { dispatch } from '../../store';

import Tooltip from '../tooltip';

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  displayByEmissions: state.application.tableDisplayEmissions,
  exchangeKey: state.application.tooltipDisplayMode,
  visible: getSelectedZoneExchangeKeys(state).includes(state.application.tooltipDisplayMode),
  zoneData: state.application.tooltipZoneData,
});

const CountryPanelExchangeTooltip = ({
  colorBlindModeEnabled,
  displayByEmissions,
  exchangeKey,
  visible,
  zoneData,
}) => {
  const headlineRef = useRef(null);

  if (!visible) return null;

  const co2color = getCo2Scale(colorBlindModeEnabled);

  let value = zoneData.exchange[exchangeKey];

  const isExport = value < 0;
  const co2intensity = zoneData.exchangeCo2Intensities[exchangeKey];

  const totalPositive = displayByEmissions
    ? (zoneData.totalCo2Production + zoneData.totalCo2Discharge + zoneData.totalCo2Import) // gCO2eq/h
    : (zoneData.totalProduction + zoneData.totalDischarge + zoneData.totalImport);

  value = displayByEmissions ? (value * 1000 * co2intensity) : value;
  const isNull = !isFinite(value) || value === undefined;

  const format = displayByEmissions ? formatCo2 : formatPower;

  const absFlow = Math.abs(value);
  const exchangeProportion = !isNull ? Math.round(absFlow / totalPositive * 100.0) : '?';

  // Exchange
  const langString = isExport
    ? (displayByEmissions ? 'emissionsExportedTo' : 'electricityExportedTo')
    : (displayByEmissions ? 'emissionsImportedFrom' : 'electricityImportedFrom');

  // Capacity
  const absCapacity = Math.abs(((zoneData.exchangeCapacities || {})[exchangeKey] || [])[isExport ? 0 : 1]);
  const hasCapacity = absCapacity !== undefined && isFinite(absCapacity);
  const capacityFactor = (hasCapacity && Math.round(absFlow / absCapacity * 100)) || '?';

  // Carbon intensity
  const o = isExport ? zoneData.countryCode : exchangeKey;

  dispatch({ type: 'SET_CO2_COLORBAR_MARKER', payload: { marker: co2intensity } });

  setTimeout(() => {
    modifyDOM(headlineRef, '#country-flag', (img) => { img.src = flagUri(zoneData.countryCode); });
    modifyDOM(headlineRef, '#country-exchange-flag', (img) => { img.src = flagUri(exchangeKey); });
  }, 50);

  return (
    <Tooltip id="countrypanel-exchange-tooltip">
      <span
        ref={headlineRef}
        dangerouslySetInnerHTML={{
          __html: co2Sub(__(
            langString,
            exchangeProportion,
            getFullZoneName(zoneData.countryCode),
            getFullZoneName(exchangeKey),
          )),
        }}
      />
      <br />
      <small>
        (
        <span
          id="exchange-proportion-detail"
          dangerouslySetInnerHTML={{
            __html: `${!isNull ? format(absFlow) : '?'} / ${!isNull ? format(totalPositive) : '?'}`,
          }}
        />
        )
      </small>
      <br />
      {!displayByEmissions && (
        <span className="production-visible">
          <br />
          {__('tooltips.utilizing')}
          {' '}
          <b><span id="capacity-factor">{capacityFactor}%</span></b>
          {' '}
          {__('tooltips.ofinstalled')}
          <br />
          <small>
            (
            <span id="capacity-factor-detail">
              {format(absFlow) || '?'} / {(hasCapacity && format(absCapacity)) || '?'}
            </span>
            )
          </small>
          <br />
          <br />
          <span dangerouslySetInnerHTML={{ __html: co2Sub(__('tooltips.withcarbonintensity')) }} />
          <br />
          <img className="country-exchange-source-flag flag" alt="" src={flagUri(o)} />
          {' '}
          <b><span className="country-exchange-source-name">{getFullZoneName(o)}</span></b>
          : 
          <div className="emission-rect" style={{ backgroundColor: co2intensity ? co2color(co2intensity) : 'gray' }} />
          {' '}
          <span className="emission-intensity">{Math.round(co2intensity) || '?'}</span>
          gCO
          <span className="sub">2</span>
          eq/kWh
          <br />
        </span>
      )}
    </Tooltip>
  );
};

export default connect(mapStateToProps)(CountryPanelExchangeTooltip);
