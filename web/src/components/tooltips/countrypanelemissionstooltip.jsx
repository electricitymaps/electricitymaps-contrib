import React from 'react';

import { useTranslation } from '../../helpers/translation';
import { getTotalElectricity } from '../../helpers/zonedata';
import { tonsPerHourToGramsPerMinute } from '../../helpers/math';
import Tooltip from '../tooltip';
import { TimeDisplay } from '../timeDisplay';
import styled from 'styled-components';

const StyledTimeDisplay = styled(TimeDisplay)`
  font-size: smaller;
  margin-top: 0px;
  font-weight: 600;
`;

const CountryPanelEmissionsTooltip = ({ position, zoneData, onClose }) => {
  const { __ } = useTranslation();
  if (!zoneData) {
    return null;
  }

  const totalEmissions = Math.round(tonsPerHourToGramsPerMinute(getTotalElectricity(zoneData, true)) * 100) / 100;

  return (
    <Tooltip id="countrypanel-emissions-tooltip" position={position} onClose={onClose}>
      <StyledTimeDisplay date={zoneData.stateDatetime} />
      <b>{totalEmissions}t</b> {__('ofCO2eqPerMinute')}
    </Tooltip>
  );
};

export default CountryPanelEmissionsTooltip;
