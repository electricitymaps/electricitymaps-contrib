import React from 'react';
import { connect } from 'react-redux';

import { EMISSIONS_GRAPH_LAYER_KEY } from '../../helpers/constants';

import { __ } from '../../helpers/translation';
import { getTotalElectricity } from '../../helpers/zonedata';
import { tonsPerHourToGramsPerMinute } from '../../helpers/math';
import { co2Sub } from '../../helpers/formatting';
import Tooltip from '../tooltip';

const mapStateToProps = state => ({
  visible: state.application.tooltipDisplayMode === EMISSIONS_GRAPH_LAYER_KEY,
  zoneData: state.application.tooltipData,
});

const CountryPanelEmissionsTooltip = ({ visible, zoneData }) => {
  if (!visible) return null;

  const totalEmissions = Math.round(tonsPerHourToGramsPerMinute(getTotalElectricity(zoneData, true)) * 100) / 100;

  return (
    <Tooltip id="countrypanel-emissions-tooltip">
      <b>{totalEmissions}t</b> <span dangerouslySetInnerHTML={{ __html: co2Sub(__('ofCO2eqPerMinute')) }} />
    </Tooltip>
  );
};

export default connect(mapStateToProps)(CountryPanelEmissionsTooltip);
