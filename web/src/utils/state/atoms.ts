import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { dateToDatetimeString } from 'utils/helpers';

import {
  Mode,
  SpatialAggregate,
  ThemeOptions,
  TimeAverages,
  ToggleOptions,
} from '../constants';

// TODO: Move these atoms to relevant features
// TODO: Make some of these atoms also sync with URL (see atomWithCustomStorage.ts)

export const timeAverageAtom = atom(TimeAverages.HOURLY);
export const isHourlyAtom = atom((get) => get(timeAverageAtom) === TimeAverages.HOURLY);

// TODO: consider another initial value
export const selectedDatetimeIndexAtom = atom({ datetime: new Date(), index: 0 });

export const selectedDatetimeStringAtom = atom((get) => {
  const { datetime } = get(selectedDatetimeIndexAtom);
  return dateToDatetimeString(datetime);
});

export const spatialAggregateAtom = atomWithStorage(
  'country-mode',
  SpatialAggregate.ZONE
);
export const productionConsumptionAtom = atomWithStorage('mode', Mode.CONSUMPTION);

export const solarLayerAtom = atomWithStorage('solar', ToggleOptions.OFF);
export const isSolarLayerEnabledAtom = atom(
  (get) =>
    get(isHourlyAtom) &&
    get(solarLayerAtom) === ToggleOptions.ON &&
    get(selectedDatetimeIndexAtom).index === 24
);

export const windLayerAtom = atomWithStorage('wind', ToggleOptions.OFF);
export const isWindLayerEnabledAtom = atom(
  (get) =>
    get(isHourlyAtom) &&
    get(windLayerAtom) === ToggleOptions.ON &&
    get(selectedDatetimeIndexAtom).index === 24
);

export const solarLayerLoadingAtom = atom(false);
export const windLayerLoadingAtom = atom(false);

export const displayByEmissionsAtom = atom(false);

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

export const dataSourcesCollapsedBarBreakdown = atom(true);

export const dataSourcesCollapsedBreakdown = atom(true);

export const dataSourcesCollapsedEmission = atom(true);

export const userLocationAtom = atom(undefined);

export const hasSeenSurveyCardAtom = atomWithStorage('hasSeenSurveyCard', false);
