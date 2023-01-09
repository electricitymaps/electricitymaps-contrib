import React from 'react';
import { useSelector } from 'react-redux';
import { formatDate } from '../../helpers/formatting';
import { useTranslation } from '../../helpers/translation';

import Tooltip from '../tooltip';

const TimeSliderTooltip = ({ position, onClose, date, disabled }) => {
  const { i18n } = useTranslation();
  const selectedTimeAggregate = useSelector((state) => state.application.selectedTimeAggregate);
  if (disabled) {
    return null;
  }

  return (
    <Tooltip id="timeslider-tooltip" position={position} onClose={onClose}>
      {formatDate(date, i18n.language, selectedTimeAggregate)}
    </Tooltip>
  );
};

export default TimeSliderTooltip;
