import React from 'react';
import { connect } from 'react-redux';
import { isFinite } from 'lodash';

import { modeOrder } from '../../helpers/constants';
import { __, getFullZoneName } from '../../helpers/translation';
import { formatCo2, formatPower } from '../../helpers/formatting';
import { flagUri } from '../../helpers/flags';
import { getRatioPercent } from '../../helpers/math';

import Tooltip from '../tooltip';
import { CarbonIntensity, MetricRatio } from './common';
import { getProductionCo2Intensity, getTotalElectricity } from '../../helpers/zonedata';

const mapStateToProps = state => ({
  displayByEmissions: state.application.tableDisplayEmissions,
});

const CountryPanelProductionTooltip = ({
  displayByEmissions,
  mode,
  position,
  zoneData,
}) => {
  if (!zoneData) return null;

  const co2Intensity = getProductionCo2Intensity(mode, zoneData);

  const format = displayByEmissions ? formatCo2 : formatPower;

  const isStorage = mode.indexOf('storage') !== -1;
  const resource = mode.replace(' storage', '');

  const capacity = (zoneData.capacity || {})[mode];
  const production = (zoneData.production || {})[resource];
  const storage = (zoneData.storage || {})[resource];

  const electricity = isStorage ? -storage : production;
  const isExport = electricity < 0;

  const usage = Math.abs(displayByEmissions ? (electricity * co2Intensity * 1000) : electricity);
  const totalElectricity = getTotalElectricity(zoneData, displayByEmissions);

  const co2IntensitySource = isStorage
    ? (zoneData.dischargeCo2IntensitySources || {})[resource]
    : (zoneData.productionCo2IntensitySources || {})[resource];

  let headline = __(
    isExport
      ? (displayByEmissions ? 'emissionsStoredUsing' : 'electricityStoredUsing')
      : (displayByEmissions ? 'emissionsComeFrom' : 'electricityComesFrom'),
    getRatioPercent(usage, totalElectricity),
    getFullZoneName(zoneData.countryCode),
    __(mode)
  );
  headline = headline.replace('id="country-flag"', `class="flag" src="${flagUri(zoneData.countryCode)}"`);

  return (
    <Tooltip id="countrypanel-production-tooltip" position={position}>
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
          {__('tooltips.utilizing')} <b>{getRatioPercent(usage, capacity)} %</b> {__('tooltips.ofinstalled')}
          <br />
          <MetricRatio
            value={usage}
            total={capacity}
            format={format}
          />
          <br />
          <br />
          {__('tooltips.withcarbonintensity')}
          <br />
          <CarbonIntensity intensity={co2Intensity} />
          <small> ({__('country-panel.source')}: {co2IntensitySource || '?'})</small>
        </React.Fragment>
      )}
    </Tooltip>
  );
};

export default connect(mapStateToProps)(CountryPanelProductionTooltip);
