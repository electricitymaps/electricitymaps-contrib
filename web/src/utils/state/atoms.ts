import { TIME_RANGE_TO_TIME_AVERAGE } from 'api/helpers';
import { atom, useAtom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { useCallback, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { RouteParameters } from 'types';
import { dateToDatetimeString, useNavigateWithParameters } from 'utils/helpers';

import {
  HOURLY_TIME_INDEX,
  Mode,
  SpatialAggregate,
  ThemeOptions,
  TimeRange,
  ToggleOptions,
} from '../constants';

// TODO: Move these atoms to relevant features
// TODO: Make some of these atoms also sync with URL (see atomWithCustomStorage.ts)

export const timeRangeAtom = atom<TimeRange>(TimeRange.H72);

export function useTimeRangeSync() {
  const [timeRange, setTimeRange] = useAtom(timeRangeAtom);
  const { resolution, urlTimeRange } = useParams<RouteParameters>();
  const navigateWithParameters = useNavigateWithParameters();

  useEffect(() => {
    if (resolution === 'monthly' && String(urlTimeRange) === 'all') {
      setTimeRange(TimeRange.ALL_MONTHS);
    } else if (resolution === 'yearly' && String(urlTimeRange) === 'all') {
      setTimeRange(TimeRange.ALL_YEARS);
    } else if (urlTimeRange && urlTimeRange !== timeRange) {
      setTimeRange(urlTimeRange);
    }
  }, [resolution, setTimeRange, timeRange, urlTimeRange]);

  const setTimeRangeAndNavigate = useCallback(
    (newTimeRange: TimeRange) => {
      setTimeRange(newTimeRange);
      navigateWithParameters({
        timeRange: newTimeRange,
        resolution: TIME_RANGE_TO_TIME_AVERAGE[newTimeRange],
      });
    },
    [setTimeRange, navigateWithParameters]
  );

  return [timeRange, setTimeRangeAndNavigate] as const;
}
export const isHourlyAtom = atom((get) => get(timeRangeAtom) === TimeRange.H72);

// TODO: consider another initial value
export const selectedDatetimeIndexAtom = atom({ datetime: new Date(), index: 0 });
export const endDatetimeAtom = atom<Date | undefined>(undefined);
export const startDatetimeAtom = atom<Date | undefined>(undefined);
export const selectedDatetimeStringAtom = atom<string>((get) => {
  const { datetime } = get(selectedDatetimeIndexAtom);
  return dateToDatetimeString(datetime);
});

export const spatialAggregateAtom = atom(SpatialAggregate.ZONE);
export const productionConsumptionAtom = atom(Mode.CONSUMPTION);
export const isConsumptionAtom = atom<boolean>(
  (get) => get(productionConsumptionAtom) === Mode.CONSUMPTION
);

export const areWeatherLayersAllowedAtom = atom<boolean>(
  (get) =>
    get(timeRangeAtom) === TimeRange.H72 &&
    get(selectedDatetimeIndexAtom).index === HOURLY_TIME_INDEX[TimeRange.H72]
);

export const solarLayerAtom = atomWithStorage('solar', ToggleOptions.OFF);
export const isSolarLayerEnabledAtom = atom<boolean>(
  (get) => get(solarLayerAtom) === ToggleOptions.ON && get(areWeatherLayersAllowedAtom)
);

export const windLayerAtom = atomWithStorage('wind', ToggleOptions.OFF);
export const isWindLayerEnabledAtom = atom<boolean>(
  (get) => get(windLayerAtom) === ToggleOptions.ON && get(areWeatherLayersAllowedAtom)
);

export const solarLayerLoadingAtom = atom<boolean>(false);
export const windLayerLoadingAtom = atom<boolean>(false);

export const displayByEmissionsAtom = atom<boolean>(false);

export const themeAtom = atomWithStorage('theme', ThemeOptions.SYSTEM);

export const hasOnboardingBeenSeenAtom = atomWithStorage(
  'onboardingSeen',
  localStorage.getItem('onboardingSeen') ?? false
);

export const hasEstimationFeedbackBeenSeenAtom = atomWithStorage(
  'estimationFeedbackSeen',
  localStorage.getItem('estimationFeedbackSeen') ?? false
);

export const feedbackCardCollapsedNumberAtom = atom(0);

export const colorblindModeAtom = atomWithStorage('colorblindModeEnabled', false);

export const dataSourcesCollapsedBarBreakdownAtom = atom<boolean>(true);

export const dataSourcesCollapsedBreakdownAtom = atom<boolean>(true);

export const dataSourcesCollapsedEmissionAtom = atom<boolean>(true);

export const userLocationAtom = atom<string | undefined>(undefined);

export const hasSeenSurveyCardAtom = atomWithStorage('hasSeenSurveyCard', false);

export const hasSeenUsSurveyCardAtom = atomWithStorage('hasSeenUsSurveyCard', false);

export const rankingPanelAccordionCollapsedAtom = atomWithStorage(
  'rankingPanelAccordionCollapsed',
  false
);

export const futurePriceCollapsedAtom = atom<boolean>(true);

export const isRedirectedToLatestDatetimeAtom = atom<boolean>(false);

export const openTooltipIdAtom = atom<string | null>(null);
