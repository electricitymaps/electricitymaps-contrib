import React from 'react';
import { connect } from 'react-redux';
import { isFinite } from 'lodash';

import { __, getFullZoneName } from '../../helpers/translation';
import { co2Sub, formatCo2, formatPower } from '../../helpers/formatting';
import { getCo2Scale } from '../../helpers/scales';
import { flagUri } from '../../helpers/flags';
import { getRatioPercent } from '../../helpers/math';
import { getSelectedZoneExchangeKeys } from '../../selectors';
import Tooltip from '../tooltip';

import { CarbonIntensity, MetricRatio, ZoneName } from './common';
import { getExchangeCo2Intensity, getTotalElectricity } from '../../helpers/zonedata';

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  displayByEmissions: state.application.tableDisplayEmissions,
  electricityMixMode: state.application.electricityMixMode,
  exchangeKey: state.application.tooltipDisplayMode,
  visible: getSelectedZoneExchangeKeys(state).includes(state.application.tooltipDisplayMode),
  zoneData: state.application.tooltipZoneData,
});

const CountryPanelExchangeTooltip = ({
  colorBlindModeEnabled,
  displayByEmissions,
  electricityMixMode,
  exchangeKey,
  visible,
  zoneData,
}) => {
  if (!visible || !zoneData) return null;

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const co2Intensity = getExchangeCo2Intensity(exchangeKey, zoneData, electricityMixMode);

  const format = displayByEmissions ? formatCo2 : formatPower;

  const exchangeCapacityRange = (zoneData.exchangeCapacities || {})[exchangeKey];
  const exchange = (zoneData.exchange || {})[exchangeKey];

  const isExport = exchange < 0;

  const usage = Math.abs(displayByEmissions ? (exchange * 1000 * co2Intensity) : exchange);
  const totalElectricity = getTotalElectricity(zoneData, displayByEmissions);
  const totalCapacity = Math.abs((exchangeCapacityRange || [])[isExport ? 0 : 1]);

  let headline = co2Sub(__(
    isExport
      ? (displayByEmissions ? 'emissionsExportedTo' : 'electricityExportedTo')
      : (displayByEmissions ? 'emissionsImportedFrom' : 'electricityImportedFrom'),
    getRatioPercent(usage, totalElectricity),
    getFullZoneName(zoneData.countryCode),
    getFullZoneName(exchangeKey)
  ));
  headline = headline.replace('id="country-flag"', `class="flag" src="${flagUri(zoneData.countryCode)}"`);
  headline = headline.replace('id="country-exchange-flag"', `class="flag" src="${flagUri(exchangeKey)}"`);

  return (
    <Tooltip id="countrypanel-exchange-tooltip">
      <span dangerouslySetInnerHTML={{ __html: headline }} />
      <br />
      <MetricRatio
        value={usage}
        total={totalElectricity}
        format={format}
      />
      {!displayByEmissions && (
        <React.Fragment>
          <br />
          <br />
          {__('tooltips.utilizing')} <b>{getRatioPercent(usage, totalCapacity)} %</b> {__('tooltips.ofinstalled')}
          <br />
          <MetricRatio
            value={usage}
            total={totalCapacity}
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
            intensity={co2Intensity}
          />
        </React.Fragment>
      )}
    </Tooltip>
  );
};

export default connect(mapStateToProps)(CountryPanelExchangeTooltip);
