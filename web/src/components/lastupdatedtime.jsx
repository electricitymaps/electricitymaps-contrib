import React, { useEffect, useState } from 'react';
import { differenceInHours } from 'date-fns';

import { useCurrentDatetimes } from '../hooks/redux';
import { useTranslation } from '../helpers/translation';
import { useSelector } from 'react-redux';
import { TIME } from '../helpers/constants';

const LastUpdatedTime = () => {
  const [style, setStyle] = useState({});
  const timestamp = useCurrentDatetimes().at(-1);
  const selectedTimeAggregate = useSelector((state) => state.application.selectedTimeAggregate);
  const { i18n } = useTranslation();

  // Every time the timestamp gets changed, jump to the highlighted state
  // and slowly release back to standard text from the next render cycle.
  useEffect(() => {
    setStyle({ color: 'darkred' });
    setTimeout(() => {
      setStyle({ transition: 'color 800ms ease-in-out' });
    }, 0);
  }, [timestamp]);

  if (!timestamp || selectedTimeAggregate !== TIME.HOURLY) {
    // last updated currently does not work for other time aggregates
    return null;
  }

  return (
    <span style={style}>
      {new Intl.RelativeTimeFormat(i18n.language).format(differenceInHours(timestamp, Date.now()), 'hour')}
    </span>
  );
};

export default LastUpdatedTime;
