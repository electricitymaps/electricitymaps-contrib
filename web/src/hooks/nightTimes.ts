import useGetZone from 'api/getZone';
import {
  addDays,
  closestIndexTo,
  compareAsc,
  isAfter,
  isBefore,
  max,
  min,
  subDays,
} from 'date-fns';
import { useGetGeometries } from 'features/map/map-utils/getMapGrid';
import { useEffect, useState } from 'react';
import { getSunrise, getSunset } from 'sunrise-sunset-js';
import { getZoneFromPath } from 'utils/helpers';

export function useNightTimes() {
  const { data } = useGetZone();
  const { worldGeometries } = useGetGeometries();
  const zoneId = getZoneFromPath();
  const [nightTimes, setNightTimes] = useState<number[][] | undefined>(undefined);

  useEffect(() => {
    if (zoneId && data) {
      // get latitude and longitude of zone
      const feature = worldGeometries.features.find(
        (feature) => feature.properties.zoneId === zoneId
      );
      const coord = feature?.properties.center;
      if (!coord) {
        console.warn('no center coordinates available');
        return undefined;
      }
      const [longitude, latitude] = coord;

      const datetimes = Object.keys(data.zoneStates)
        .map((d) => new Date(d))

        .sort(compareAsc);

      // This needs to be exactly 25, otherwise the nightTimes calculation will return incorrect values
      // TODO: We should consider not using the actual datetimes sent from backend
      if (datetimes.length === 25) {
        setNightTimes(calculateNightTimes(datetimes, latitude, longitude));
      } else {
        setNightTimes(undefined);
      }
    }
  }, [zoneId, data]);

  return nightTimes;
}

/** Returns indexes of when nights start and end in the given datetimes */
export function calculateNightTimes(
  datetimes: Date[],
  latitude: number,
  longitude: number
) {
  const first = min(datetimes);
  const last = max(datetimes);
  const nightTimes = [];

  for (let date = last; !isBefore(date, first); date = subDays(date, 1)) {
    const nightStart = getSunset(latitude, longitude, date);
    let nightEnd = getSunrise(latitude, longitude, date);

    // Due to some bug in the library, sometimes we get nightStart > nightEnd
    if (nightStart.getTime() > nightEnd.getTime()) {
      nightEnd = addDays(nightEnd, 1);
    }

    // Only use nights that start before the latest time we have
    // and that finishes after the earliest time we have
    if (isBefore(nightStart, last) && isAfter(nightEnd, first)) {
      nightTimes.push([
        closestIndexTo(nightStart, datetimes) as number,
        closestIndexTo(nightEnd, datetimes) as number,
      ]);
    }
  }
  return nightTimes.sort();
}
