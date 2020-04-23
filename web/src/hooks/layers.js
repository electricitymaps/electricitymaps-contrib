import React, { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { interpolate } from 'd3-interpolate';
import { values } from 'lodash';
import moment from 'moment';

import { useCustomDatetime } from '../helpers/router';
import { getRefTime, getTargetTime } from '../helpers/grib';

export function useInterpolateWindData() {
  const windData = useSelector(state => state.data.wind);
  const customDatetime = useCustomDatetime();

  return useMemo(
    () => {
      if (!windData || !windData.forecasts) {
        return null;
      }

      const gribs1 = windData.forecasts[0];
      const gribs2 = windData.forecasts[1];
      const tBefore = getTargetTime(gribs1[0]);
      const tAfter = getTargetTime(gribs2[0]);
      const datetime = moment(customDatetime || new Date()); 
      const k = (datetime - tBefore) / (tAfter - tBefore);

      if (datetime > tAfter) {
        console.error('Error while interpolating wind because current time is out of bounds');
        return null;
      }

      console.log(`#1 wind forecast target ${tBefore.fromNow()} made ${getRefTime(gribs1[0]).fromNow()}`);
      console.log(`#2 wind forecast target ${tAfter.fromNow()} made ${getRefTime(gribs2[0]).fromNow()}`);

      return [
        { ...gribs1[0], data: gribs1[0].data.map((d, i) => interpolate(d, gribs2[0].data[i])(k)) },
        { ...gribs1[1], data: gribs1[1].data.map((d, i) => interpolate(d, gribs2[1].data[i])(k)) },
      ];
    },
    [windData, customDatetime],
  );
}

export function useExchangeArrowsData() {
  const isConsumption = useSelector(state => state.application.electricityMixMode === 'consumption');
  const exchanges = useSelector(state => state.data.grid.exchanges);

  return useMemo(
    () => (isConsumption ? values(exchanges).filter(d => d.lonlat) : []),
    [isConsumption, exchanges],
  );
}
