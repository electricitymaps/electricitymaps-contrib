import React from 'react';

import { useTranslation } from '../../helpers/translation';
import Tooltip from '../tooltip';

const LowCarbonInfoTooltip = ({ position, onClose }) => {
  const { __ } = useTranslation();
  return (
    <Tooltip id="lowcarb-info-tooltip" position={position} onClose={onClose}>
      <b>{__('tooltips.lowcarbon')}</b>
      <br />
      <small>{__('tooltips.lowCarbDescription')}</small>
      <br />
    </Tooltip>
  );
};

export default LowCarbonInfoTooltip;
