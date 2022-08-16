import { useSelector } from 'react-redux';
import { useTranslation } from '../helpers/translation';
import { formatDate } from '../helpers/formatting';
import React from 'react';
import { useCurrentDatetimes } from '../hooks/redux';

export const TimeDisplay = ({ className, date }: any) => {
  // if no date is provided, will use the current zonetime
  const datetimes = useCurrentDatetimes();
  const selectedZoneTimeIndex = useSelector((state) => (state as any).application.selectedZoneTimeIndex);
  const { i18n } = useTranslation();
  const selectedTimeAggregate = useSelector((state) => (state as any).application.selectedTimeAggregate);

  const shownDatetime = date ? date : datetimes[selectedZoneTimeIndex];

  return <p className={className}>{formatDate(shownDatetime, i18n.language, selectedTimeAggregate)}</p>;
};
