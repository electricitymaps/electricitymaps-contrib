import React from 'react';
import { connect } from 'react-redux';

import { useTranslation, getZoneNameWithCountry } from '../../helpers/translation';
import { formatCo2, formatPower } from '../../helpers/formatting';
import { flagUri } from '../../helpers/flags';
import { getRatioPercent } from '../../helpers/math';

import Tooltip from '../tooltip';
import { CarbonIntensity, MetricRatio } from './common';
import { getElectricityProductionValue, getProductionCo2Intensity, getTotalElectricity } from '../../helpers/zonedata';

const mapStateToProps = (state) => ({
  displayByEmissions: state.application.tableDisplayEmissions,
});

const CountryPanelProductionTooltip = ({ displayByEmissions, mode, position, zoneData, onClose }) => {
  const { __ } = useTranslation();
  if (!zoneData) {
    return null;
  }

  const co2Intensity = getProductionCo2Intensity(mode, zoneData);

  const format = displayByEmissions ? formatCo2 : formatPower;

  const isStorage = mode.indexOf('storage') !== -1;
  const resource = mode.replace(' storage', '');

  const capacity = (zoneData.capacity || {})[mode];
  const production = (zoneData.production || {})[resource];
  const storage = (zoneData.storage || {})[resource];

  const electricity = getElectricityProductionValue({
    capacity,
    isStorage,
    storage,
    production,
  });
  const isExport = electricity < 0;

  const usage =
    Number.isFinite(electricity) && Math.abs(displayByEmissions ? electricity * co2Intensity * 1000 : electricity);
  const totalElectricity = getTotalElectricity(zoneData, displayByEmissions);

  const emissions = Number.isFinite(electricity) && Math.abs(electricity * co2Intensity * 1000);
  const totalEmissions = getTotalElectricity(zoneData, true);

  const co2IntensitySource = isStorage
    ? (zoneData.dischargeCo2IntensitySources || {})[resource]
    : (zoneData.productionCo2IntensitySources || {})[resource];

  const getTranslatedText = () => {
    if (isExport) {
      return displayByEmissions ? 'emissionsStoredUsing' : 'electricityStoredUsing';
    } else {
      return displayByEmissions ? 'emissionsComeFrom' : 'electricityComesFrom';
    }
  };

  let headline = __(
    getTranslatedText(),
    getRatioPercent(usage, totalElectricity),
    getZoneNameWithCountry(zoneData.countryCode),
    __(mode)
  );
  headline = headline.replace('id="country-flag"', `class="flag" src="${flagUri(zoneData.countryCode)}"`);

  return (
    <Tooltip id="countrypanel-production-tooltip" position={position} onClose={onClose}>
      <span dangerouslySetInnerHTML={{ __html: headline }} />
      <br />
      <MetricRatio value={usage} total={totalElectricity} format={format} />
      {!displayByEmissions && (
        <React.Fragment>
          <br />
          <br />
          {__('tooltips.utilizing')} <b>{getRatioPercent(usage, capacity)} %</b> {__('tooltips.ofinstalled')}
          <br />
          <MetricRatio value={usage} total={capacity} format={format} />
          <br />
          <br />
          {__('tooltips.representing')} <b>{getRatioPercent(emissions, totalEmissions)} %</b>{' '}
          {__('tooltips.ofemissions')}
          <br />
          <MetricRatio value={emissions} total={totalEmissions} format={formatCo2} />
        </React.Fragment>
      )}
      {/* Don't show carbon intensity if we know for sure the zone doesn't use this resource */}
      {!displayByEmissions && (Number.isFinite(co2Intensity) || usage !== 0) && (
        <React.Fragment>
          <br />
          <br />
          {__('tooltips.withcarbonintensity')}
          <br />
          <CarbonIntensity intensity={co2Intensity} />
          <small>
            {' '}
            ({__('country-panel.source')}: {co2IntensitySource || '?'})
          </small>
        </React.Fragment>
      )}
    </Tooltip>
  );
};

export default connect(mapStateToProps)(CountryPanelProductionTooltip);
