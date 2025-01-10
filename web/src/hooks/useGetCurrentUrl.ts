import { useAtomValue } from 'jotai';
import { useParams } from 'react-router-dom';
import { RouteParameters } from 'types';
import { baseUrl } from 'utils/constants';
import { selectedDatetimeIndexAtom } from 'utils/state/atoms';

export function useGetCurrentUrl() {
  const { resolution, urlTimeRange, zoneId } = useParams<RouteParameters>();
  const selectedDatetime = useAtomValue(selectedDatetimeIndexAtom);
  const datetime = selectedDatetime.datetime ?? new Date(selectedDatetime.datetime);

  const url =
    baseUrl +
    (zoneId
      ? `/zone/${zoneId}/${urlTimeRange}/${resolution}/${datetime.toISOString()}`
      : '/map/72h/hourly');

  return url;
}
