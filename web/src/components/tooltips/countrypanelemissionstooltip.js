import React from 'react';
import { connect } from 'react-redux';

import { __ } from '../../helpers/translation';
import { getTotalElectricity } from '../../helpers/zonedata';
import { tonsPerHourToGramsPerMinute } from '../../helpers/math';
import { co2Sub } from '../../helpers/formatting';
import Tooltip from '../tooltip';

const CountryPanelEmissionsTooltip = ({ position, zoneData }) => {
  if (!zoneData) return null;

  const totalEmissions = Math.round(tonsPerHourToGramsPerMinute(getTotalElectricity(zoneData, true)) * 100) / 100;

  return (
    <Tooltip id="countrypanel-emissions-tooltip" position={position}>
      <b>{totalEmissions}t</b> <span dangerouslySetInnerHTML={{ __html: co2Sub(__('ofCO2eqPerMinute')) }} />
    </Tooltip>
  );
};

export default CountryPanelEmissionsTooltip;
