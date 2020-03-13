import React, { useRef } from 'react';
import { connect } from 'react-redux';
import { isFinite } from 'lodash';

import { modeOrder } from '../../helpers/constants';
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
  electricityMixMode: state.application.electricityMixMode,
  mode: state.application.tooltipDisplayMode,
  visible: modeOrder.includes(state.application.tooltipDisplayMode),
  zoneData: state.application.tooltipZoneData,
});

const CountryPanelProductionTooltip = ({
  colorBlindModeEnabled,
  displayByEmissions,
  exchangeKey,
  mode,
  visible,
  zoneData,
}) => {
  const headlineRef = useRef(null);

  if (!visible || !zoneData || !zoneData.productionCo2Intensities) return null;

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);

  const isStorage = mode.indexOf('storage') !== -1;
  const resource = mode.replace(' storage', '');

  let value = isStorage
    ? -zoneData.storage[resource]
    : zoneData.production[resource];

  const isExport = value < 0;

  const co2intensity = !isExport && (
    isStorage
      ? zoneData.dischargeCo2Intensities[resource]
      : zoneData.productionCo2Intensities[resource]
  );
  const co2intensitySource = !isExport && (
    isStorage
      ? zoneData.dischargeCo2IntensitySources[resource]
      : zoneData.productionCo2IntensitySources[resource]
  );

  if (co2intensity) {
    dispatch({ type: 'SET_CO2_COLORBAR_MARKER', payload: { marker: co2intensity } });
  }

  if (displayByEmissions && !isExport) {
    value *= co2intensity * 1000.0; // MW * gCO2/kWh * 1000 --> gCO2/h
  }

  const absValue = Math.abs(value);
  const format = displayByEmissions ? formatCo2 : formatPower;

  const capacity = (zoneData.capacity || {})[mode];
  const hasCapacity = capacity !== undefined && capacity >= (zoneData.production[mode] || 0);
  const capacityFactor = (hasCapacity && absValue !== null)
    ? Math.round(absValue / capacity * 10000) / 100
    : '?';

  const totalPositive = displayByEmissions
    ? (zoneData.totalCo2Production + zoneData.totalCo2Discharge + zoneData.totalCo2Import) // gCO2eq/h
    : (zoneData.totalProduction + zoneData.totalDischarge + zoneData.totalImport);

  const isNull = !isFinite(absValue) || absValue === undefined;

  const productionProportion = !isNull ? Math.round(absValue / totalPositive * 10000) / 100 : '?';

  const langString = isExport
    ? (displayByEmissions ? 'emissionsStoredUsing' : 'electricityStoredUsing')
    : (displayByEmissions ? 'emissionsComeFrom' : 'electricityComesFrom');

  setTimeout(() => {
    modifyDOM(headlineRef, '#country-flag', (img) => { img.src = flagUri(zoneData.countryCode); });
  }, 50);

  return (
    <Tooltip id="countrypanel-production-tooltip">
      <span
        ref={headlineRef}
        dangerouslySetInnerHTML={{
          __html: co2Sub(__(
            langString,
            productionProportion,
            getFullZoneName(zoneData.countryCode),
            __(mode),
          )),
        }}
      />
      <br />
      <small>
        (
        <span
          id="production-proportion-detail"
          dangerouslySetInnerHTML={{
            __html: `${!isNull ? format(absValue) : '?'} / ${!isNull ? format(totalPositive) : '?'}`,
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
          <b><span id="capacity-factor">{capacityFactor} %</span></b>
          {' '}
          {__('tooltips.ofinstalled')}
          <br />
          <small>
            (
            <span id="capacity-factor-detail">
              {format(absValue) || '?'} / {(hasCapacity && format(capacity)) || '?'}
            </span>
            )
          </small>
          <br />
          <br />
          <span dangerouslySetInnerHTML={{ __html: co2Sub(__('tooltips.withcarbonintensity')) }} />
          <br />
          <div className="emission-rect" style={{ backgroundColor: co2ColorScale(co2intensity) }} />
          {' '}
          <span className="emission-intensity">{Math.round(co2intensity) || '?'}</span>
          gCO
          <span className="sub">2</span>
          {'eq/kWh '}
          <small>
            (
            {__('country-panel.source')}
            {': '}
            <span className="emission-source">{co2intensitySource || '?'}</span>
            )
          </small>
        </span>
      )}
    </Tooltip>
  );
};

export default connect(mapStateToProps)(CountryPanelProductionTooltip);
