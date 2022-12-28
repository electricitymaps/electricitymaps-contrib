import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { Mode, ThemeOptions, TimeAverages, ToggleOptions } from '../constants';
import atomWithCustomStorage from './atomWithCustomStorage';

// TODO: Ensure it works as intended without URL params
export const timeAverageAtom = atomWithCustomStorage<TimeAverages>({
  key: 'average',
  initialValue: TimeAverages.HOURLY,
  options: {
    syncWithUrl: true,
    syncWithLocalStorage: true,
  },
});

// TODO consider another initial value
export const selectedDatetimeIndexAtom = atom({ datetimeString: '', index: 0 });

export const spatialAggregateAtom = atomWithCustomStorage<ToggleOptions>({
  key: 'country-mode',
  initialValue: ToggleOptions.OFF,
  options: {
    syncWithUrl: true,
    syncWithLocalStorage: true,
  },
});

export const solarLayerEnabledAtom = atomWithCustomStorage<ToggleOptions>({
  key: 'solar',
  initialValue: ToggleOptions.OFF,
  options: {
    syncWithUrl: true,
    syncWithLocalStorage: true,
  },
});
export const solarLayerLoadingAtom = atom(false);

export const windLayerAtom = atomWithCustomStorage<ToggleOptions>({
  key: 'wind',
  initialValue: ToggleOptions.OFF,
  options: {
    syncWithUrl: true,
    syncWithLocalStorage: true,
  },
});
export const windLayerLoadingAtom = atom(false);

export const displayByEmissionsAtom = atom(false);

export const productionConsumptionAtom = atomWithCustomStorage<Mode>({
  key: 'mode',
  initialValue: Mode.CONSUMPTION,
  options: {
    syncWithUrl: true,
    syncWithLocalStorage: true,
  },
});

export const themeAtom = atomWithStorage('theme', ThemeOptions.LIGHT);

export const hasOnboardingBeenSeenAtom = atomWithCustomStorage({
  key: 'onboardingSeen',
  initialValue: 'false',
  options: {
    syncWithLocalStorage: true,
  },
});

export const colorblindModeAtom = atomWithCustomStorage({
  key: 'colorblindModeEnabled',
  initialValue: 'false',
  options: {
    syncWithLocalStorage: true,
  },
});
