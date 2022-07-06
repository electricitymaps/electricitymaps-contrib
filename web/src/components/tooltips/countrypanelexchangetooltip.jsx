import React from 'react';
import { connect } from 'react-redux';

import { useTranslation, getZoneNameWithCountry } from '../../helpers/translation';
import { formatCo2, formatPower } from '../../helpers/formatting';
import { flagUri } from '../../helpers/flags';
import { getRatioPercent } from '../../helpers/math';
import Tooltip from '../tooltip';

import { CarbonIntensity, MetricRatio, ZoneName } from './common';
import { getExchangeCo2Intensity, getTotalElectricity } from '../../helpers/zonedata';

const mapStateToProps = (state) => ({
  displayByEmissions: state.application.tableDisplayEmissions,
  electricityMixMode: state.application.electricityMixMode,
});

const CountryPanelExchangeTooltip = ({
  displayByEmissions,
  electricityMixMode,
  exchangeKey,
  position,
  zoneData,
  onClose,
}) => {
  const { __ } = useTranslation();
  if (!zoneData) {
    return null;
  }

  const co2Intensity = getExchangeCo2Intensity(exchangeKey, zoneData, electricityMixMode);

  const format = displayByEmissions ? formatCo2 : formatPower;

  const exchangeCapacityRange = (zoneData.exchangeCapacities || {})[exchangeKey];
  const exchange = (zoneData.exchange || {})[exchangeKey];

  const isExport = exchange < 0;

  const usage = Math.abs(displayByEmissions ? exchange * 1000 * co2Intensity : exchange);
  const totalElectricity = getTotalElectricity(zoneData, displayByEmissions);
  const totalCapacity = Math.abs((exchangeCapacityRange || [])[isExport ? 0 : 1]);

  const emissions = Math.abs(exchange * 1000 * co2Intensity);
  const totalEmissions = getTotalElectricity(zoneData, true);
  const getTranslatedText = () => {
    if (isExport) {
      return displayByEmissions ? 'emissionsExportedTo' : 'electricityExportedTo';
    } else {
      return displayByEmissions ? 'emissionsImportedFrom' : 'electricityImportedFrom';
    }
  };

  let headline = __(
    getTranslatedText(),
    getRatioPercent(usage, totalElectricity),
    getZoneNameWithCountry(zoneData.countryCode),
    getZoneNameWithCountry(exchangeKey)
  );
  headline = headline.replace('id="country-flag"', `class="flag" src="${flagUri(zoneData.countryCode)}"`);
  headline = headline.replace('id="country-exchange-flag"', `class="flag" src="${flagUri(exchangeKey)}"`);

  return (
    <Tooltip id="countrypanel-exchange-tooltip" position={position} onClose={onClose}>
      <span dangerouslySetInnerHTML={{ __html: headline }} />
      <br />
      <MetricRatio value={usage} total={totalElectricity} format={format} />
      {!displayByEmissions && (
        <React.Fragment>
          <br />
          <br />
          {__('tooltips.utilizing')} <b>{getRatioPercent(usage, totalCapacity)} %</b> {__('tooltips.ofinstalled')}
          <br />
          <MetricRatio value={usage} total={totalCapacity} format={format} />
          <br />
          <br />
          {__('tooltips.representing')} <b>{getRatioPercent(emissions, totalEmissions)} %</b>{' '}
          {__('tooltips.ofemissions')}
          <br />
          <MetricRatio value={emissions} total={totalEmissions} format={formatCo2} />
          <br />
          <br />
          {__('tooltips.withcarbonintensity')}
          <br />
          <b>
            <ZoneName zone={isExport ? zoneData.countryCode : exchangeKey} />
          </b>
          : <CarbonIntensity intensity={co2Intensity} />
        </React.Fragment>
      )}
    </Tooltip>
  );
};

export default connect(mapStateToProps)(CountryPanelExchangeTooltip);
