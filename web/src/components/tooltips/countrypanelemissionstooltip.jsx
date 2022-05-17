import React from 'react';

import { useTranslation } from '../../helpers/translation';
import { getTotalElectricity } from '../../helpers/zonedata';
import { tonsPerHourToGramsPerMinute } from '../../helpers/math';
import Tooltip from '../tooltip';

const CountryPanelEmissionsTooltip = ({ position, zoneData, onClose }) => {
  const { __ } = useTranslation();
  if (!zoneData) {
    return null;
  }

  const totalEmissions = Math.round(tonsPerHourToGramsPerMinute(getTotalElectricity(zoneData, true)) * 100) / 100;

  return (
    <Tooltip id="countrypanel-emissions-tooltip" position={position} onClose={onClose}>
      <b>{totalEmissions}t</b> {__('ofCO2eqPerMinute')}
    </Tooltip>
  );
};

export default CountryPanelEmissionsTooltip;
