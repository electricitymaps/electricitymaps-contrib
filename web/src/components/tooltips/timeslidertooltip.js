import React from 'react';
import { formatHourlyDate } from '../../helpers/formatting';

import Tooltip from '../tooltip';

const TimeSliderTooltip = ({ position, onClose, date }) => {
  return (
    <Tooltip id="timeslider-tooltip" position={position} onClose={onClose}>
      {formatHourlyDate(date)}
    </Tooltip>
  );
};

export default TimeSliderTooltip;
