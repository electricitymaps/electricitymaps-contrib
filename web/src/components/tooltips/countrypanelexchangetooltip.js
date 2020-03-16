import React from 'react';
import { connect } from 'react-redux';
import { isFinite } from 'lodash';

import { __, getFullZoneName } from '../../helpers/translation';
import { co2Sub, formatCo2, formatPower } from '../../helpers/formatting';
import { getCo2Scale } from '../../helpers/scales';
import { flagUri } from '../../helpers/flags';
import { getSelectedZoneExchangeKeys } from '../../selectors';
import { dispatch } from '../../store';
import Tooltip from '../tooltip';

import { CarbonIntensity, MetricRatio, ZoneName } from './common';

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  displayByEmissions: state.application.tableDisplayEmissions,
  exchangeKey: state.application.tooltipDisplayMode,
  visible: getSelectedZoneExchangeKeys(state).includes(state.application.tooltipDisplayMode),
  zoneData: state.application.tooltipZoneData,
});

const getRatioPercent = (value, total) => {
  const perc = Math.round(value / total * 100);
  return isFinite(perc) ? `${perc} %` : '?';
};

const CountryPanelExchangeTooltip = ({
  colorBlindModeEnabled,
  displayByEmissions,
  exchangeKey,
  visible,
  zoneData,
}) => {
  if (!visible) return null;

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const format = displayByEmissions ? formatCo2 : formatPower;

  const co2intensity = (zoneData.exchangeCo2Intensities || {})[exchangeKey];
  const exchangeCapacityRange = (zoneData.exchangeCapacities || {})[exchangeKey];
  let value = (zoneData.exchange || {})[exchangeKey];

  const isExport = value < 0;

  const totalPositive = displayByEmissions
    ? (zoneData.totalCo2Production + zoneData.totalCo2Discharge + zoneData.totalCo2Import) // gCO2eq/h
    : (zoneData.totalProduction + zoneData.totalDischarge + zoneData.totalImport);

  value = displayByEmissions ? (value * 1000 * co2intensity) : value;


  const absFlow = Math.abs(value);

  // Exchange
  const langString = isExport
    ? (displayByEmissions ? 'emissionsExportedTo' : 'electricityExportedTo')
    : (displayByEmissions ? 'emissionsImportedFrom' : 'electricityImportedFrom');

  // Capacity
  const absCapacity = Math.abs((exchangeCapacityRange || [])[isExport ? 0 : 1]);

  dispatch({ type: 'SET_CO2_COLORBAR_MARKER', payload: { marker: co2intensity } });

  let headline = co2Sub(__(langString, getRatioPercent(absFlow, totalPositive), getFullZoneName(zoneData.countryCode), getFullZoneName(exchangeKey)));
  headline = headline.replace('id="country-flag"', `src="${flagUri(zoneData.countryCode)}"`);
  headline = headline.replace('id="country-exchange-flag"', `src="${flagUri(exchangeKey)}"`);

  return (
    <Tooltip id="countrypanel-exchange-tooltip">
      <span dangerouslySetInnerHTML={{ __html: headline }} />
      <br />
      <MetricRatio
        value={absFlow}
        total={totalPositive}
        format={format}
      />
      {!displayByEmissions && (
        <React.Fragment>
          <br />
          <br />
          {__('tooltips.utilizing')} <b>{getRatioPercent(absFlow, absCapacity)}</b> {__('tooltips.ofinstalled')}
          <br />
          <MetricRatio
            value={absFlow}
            total={absCapacity}
            format={format}
          />
          <br />
          <br />
          <span dangerouslySetInnerHTML={{ __html: co2Sub(__('tooltips.withcarbonintensity')) }} />
          <br />
          <b><ZoneName zone={isExport ? zoneData.countryCode : exchangeKey} /></b>
          {': '}
          <CarbonIntensity
            colorBlindModeEnabled={colorBlindModeEnabled}
            intensity={co2intensity}
          />
        </React.Fragment>
      )}
    </Tooltip>
  );
};

export default connect(mapStateToProps)(CountryPanelExchangeTooltip);
