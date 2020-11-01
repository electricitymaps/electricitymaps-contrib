import React from 'react';

import { __ } from '../../helpers/translation';
import Tooltip from '../tooltip';

const LowCarbonInfoTooltip = ({ position, onClose }) => (
  <Tooltip id="lowcarb-info-tooltip" position={position} onClose={onClose}>
    <b>{__('tooltips.lowcarbon')}</b>
    <br />
    <small>{__('tooltips.lowCarbDescription')}</small>
    <br />
  </Tooltip>
);

export default LowCarbonInfoTooltip;
