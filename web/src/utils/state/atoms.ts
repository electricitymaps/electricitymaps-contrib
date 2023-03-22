import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { Mode, ThemeOptions, TimeAverages, ToggleOptions } from '../constants';

// TODO: Move these atoms to relevant features
// TODO: Make some of these atoms also sync with URL (see atomWithCustomStorage.ts)

export const timeAverageAtom = atom(TimeAverages.HOURLY);

// TODO: consider another initial value
export const selectedDatetimeIndexAtom = atom({ datetimeString: '', index: 0 });

export const spatialAggregateAtom = atomWithStorage('country-mode', ToggleOptions.OFF);
export const productionConsumptionAtom = atomWithStorage('mode', Mode.CONSUMPTION);

export const solarLayerEnabledAtom = atomWithStorage('solar', ToggleOptions.OFF);
export const windLayerAtom = atomWithStorage('wind', ToggleOptions.OFF);
export const solarLayerLoadingAtom = atom(false);
export const windLayerLoadingAtom = atom(false);

export const displayByEmissionsAtom = atom(false);

export const themeAtom = atomWithStorage('theme', ThemeOptions.SYSTEM);

export const hasOnboardingBeenSeenAtom = atomWithStorage('onboardingSeen', false);

export const colorblindModeAtom = atomWithStorage('colorblindModeEnabled', false);
