import React from 'react';

import { __ } from '../../helpers/translation';
import Tooltip from '../tooltip';

const LowCarbonInfoTooltip = ({ position }) => (
  <Tooltip id="lowcarb-info-tooltip" position={position}>
    <b>{__('tooltips.lowcarbon')}</b>
    <br />
    <small>{__('tooltips.lowCarbDescription')}</small>
    <br />
  </Tooltip>
);

export default LowCarbonInfoTooltip;
