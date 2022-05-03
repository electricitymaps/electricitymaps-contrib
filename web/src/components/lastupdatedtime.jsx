import React, { useEffect, useState } from 'react';
import moment from 'moment';

import { useCurrentZoneHistoryEndTime } from '../hooks/redux';

const LastUpdatedTime = () => {
  const [style, setStyle] = useState({});
  const timestamp = useCurrentZoneHistoryEndTime();

  // Every time the timestamp gets changed, jump to the highlighted state
  // and slowly release back to standard text from the next render cycle.
  useEffect(() => {
    setStyle({ color: 'darkred' });
    setTimeout(() => {
      setStyle({ transition: 'color 800ms ease-in-out' });
    }, 0);
  }, [timestamp]);

  return (
    <span style={style}>
      {moment(timestamp).fromNow()}
    </span>
  );
};

export default LastUpdatedTime;
