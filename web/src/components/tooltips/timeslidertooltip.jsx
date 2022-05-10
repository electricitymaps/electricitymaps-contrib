import React from 'react';
import { useTranslation } from 'react-i18next';
import { formatHourlyDate } from '../../helpers/formatting';

import Tooltip from '../tooltip';

const TimeSliderTooltip = ({ position, onClose, date, disabled }) => {
  const { i18n } = useTranslation();
  if (disabled) return null;


  return (
    <Tooltip id="timeslider-tooltip" position={position} onClose={onClose}>
      {formatHourlyDate(date, i18n.language)}
    </Tooltip>
  );
};

export default TimeSliderTooltip;
