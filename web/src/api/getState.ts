import type { UseQueryResult } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { useAtomValue, useSetAtom } from 'jotai';
import { useEffect } from 'react';
import type { GridState } from 'types';
import { TimeAverages } from 'utils/constants';
import {
  isHourlyAtom,
  selectedDatetimeIndexAtom,
  targetDatetimeStringAtom,
  timeAverageAtom,
  urlDatetimeAtom,
} from 'utils/state/atoms';

import { cacheBuster, getBasePath, isValidDate, QUERY_KEYS } from './helpers';

const getState = async (
  timeAverage: string,
  targetDatetime?: string
): Promise<GridState> => {
  const isValidDatetime = targetDatetime && isValidDate(targetDatetime);
  const path: URL = new URL(
    `v8/state/${timeAverage}${isValidDatetime ? `?targetDate=${targetDatetime}` : ''}`,
    getBasePath()
  );

  !targetDatetime && path.searchParams.append('cacheKey', cacheBuster());
  const response = await fetch(path);
  if (response.ok) {
    const result = (await response.json()) as GridState;
    return result;
  }

  throw new Error(await response.text());
};

const useGetState = (): UseQueryResult<GridState> => {
  const setSelectedDatetimeIndex = useSetAtom(selectedDatetimeIndexAtom);

  const timeAverage = useAtomValue(timeAverageAtom);
  const isHourly = useAtomValue(isHourlyAtom);
  const urlDatetime = useAtomValue(urlDatetimeAtom);
  const targetDatetime = useAtomValue(targetDatetimeStringAtom);

  const isHistoricalQuery = Boolean(urlDatetime);
  // console.log('hi', urlDatetime);
  const shouldQueryLastHour = isHourly && !urlDatetime;

  // First fetch last hour only
  const last_hour = useQuery<GridState>({
    queryKey: [QUERY_KEYS.STATE, { aggregate: 'last_hour' }],
    queryFn: async () => getState('last_hour'),
    enabled: shouldQueryLastHour,
  });

  const hourZeroWasSuccessful = Boolean(last_hour.isLoading === false && last_hour.data);
  const shouldFetchFullState =
    isHistoricalQuery || !isHourly || hourZeroWasSuccessful || last_hour.isError === true;

  // Then fetch the rest of the data
  const all_data = useQuery<GridState>({
    queryKey: [
      QUERY_KEYS.STATE,
      {
        aggregate: timeAverage,
        targetDatetime,
      },
    ],
    queryFn: async () => getState(timeAverage, targetDatetime),
    enabled: shouldFetchFullState || isHistoricalQuery,
  });

  useEffect(() => {
    if (isHistoricalQuery && targetDatetime && all_data.data?.data?.datetimes) {
      const datetimes = Object.keys(all_data.data.data.datetimes);
      const targetDatetimeMatchingIndex =
        timeAverage === TimeAverages.HOURLY
          ? targetDatetime
          : new Date(new Date(targetDatetime).setUTCHours(0, 0, 0, 0)).toISOString();
      const targetIndex = datetimes.indexOf(targetDatetimeMatchingIndex);
      if (targetDatetime) {
        setSelectedDatetimeIndex({
          datetime: new Date(targetDatetimeMatchingIndex),
          index: targetIndex,
        });
      }
    }
  }, [
    isHistoricalQuery,
    targetDatetime,
    all_data.data,
    setSelectedDatetimeIndex,
    timeAverage,
  ]);

  return (all_data.data || !isHourly ? all_data : last_hour) as UseQueryResult<GridState>;
};

export default useGetState;
