import React, { useRef } from 'react';
import { connect } from 'react-redux';
import getSymbolFromCurrency from 'currency-symbol-map';
import { isFinite } from 'lodash';

import { __, getFullZoneName } from '../../helpers/translation';
import { co2Sub, formatCo2, formatPower } from '../../helpers/formatting';
import { getCo2Scale } from '../../helpers/scales';
import { flagUri } from '../../helpers/flags';
import { getSelectedZoneExchangeKeys } from '../../selectors';

import TooltipContainer from './tooltipcontainer';

const FLAG_SIZE = 16;

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
  const lineRef = useRef(null);
  setTimeout(() => {
    if (lineRef && lineRef.current) {
      // This seems to be the most browser-compatible way to iterate through a list of nodes.
      // See: https://developer.mozilla.org/en-US/docs/Web/API/NodeList#Example.
      Array.prototype.forEach.call(lineRef.current.querySelectorAll('#country-flag'), (img) => {
        img.src = flagUri(zoneData.countryCode, FLAG_SIZE);
      });
      Array.prototype.forEach.call(lineRef.current.querySelectorAll('#country-exchange-flag'), (img) => {
        img.src = flagUri(exchangeKey, FLAG_SIZE);
      });
    }
  }, 50);

  if (!visible) return null;

  const co2color = getCo2Scale(colorBlindModeEnabled);

  let value = zoneData.exchange[exchangeKey];

  const isExport = value < 0;
  const co2intensity = zoneData.exchangeCo2Intensities[exchangeKey];

  const totalPositive = displayByEmissions
    ? (zoneData.totalCo2Production + zoneData.totalCo2Discharge + zoneData.totalCo2Import) // gCO2eq/h
    : (zoneData.totalProduction + zoneData.totalDischarge + zoneData.totalImport);

  const domain = totalPositive;

  value = displayByEmissions ? (value * 1000 * co2intensity) : value;
  const isNull = !isFinite(value) || value === undefined;

  const format = displayByEmissions ? formatCo2 : formatPower;

  const absFlow = Math.abs(value);
  const exchangeProportion = !isNull ? Math.round(absFlow / domain * 100.0) : '?';

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

  // TODO
  // if (co2Colorbars) co2Colorbars.forEach((d) => { d.currentMarker(co2intensity); });

  return (
    <TooltipContainer id="countrypanel-exchange-tooltip">
      <span
        id="line1"
        ref={lineRef}
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
        <span id="exchange-proportion-detail">
          {!isNull ? format(absFlow) : '?'} / {!isNull ? format(domain) : '?'}
        </span>
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
          <img className="country-exchange-source-flag flag" alt="" src={flagUri(o, FLAG_SIZE)} />
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
    </TooltipContainer>
  );
};

export default connect(mapStateToProps)(CountryPanelExchangeTooltip);
