import React from 'react';
import { formatDate } from '../../helpers/formatting';
import { useTranslation } from '../../helpers/translation';

import Tooltip from '../tooltip';

const TimeSliderTooltip = ({ position, onClose, date, disabled }) => {
  const { i18n } = useTranslation();
  if (disabled) {
    return null;
  }

  return (
    <Tooltip id="timeslider-tooltip" position={position} onClose={onClose}>
      {formatDate(date, i18n.language)}
    </Tooltip>
  );
};

export default TimeSliderTooltip;
