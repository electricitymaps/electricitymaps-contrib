import { atom } from 'jotai';
import { atomWithStorage, createJSONStorage } from 'jotai/utils';
import { ThemeOptions, TimeAverages, ToggleOptions } from '../constants';
import atomWithCustomStorage from './atomWithCustomStorage';

// TODO: Fix typing such that we don't need to cast to TimeAverage
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
export const selectedDatetimeIndexAtom = atom('');
selectedDatetimeIndexAtom.debugLabel = 'selectedDatetimeIndex';

/** Some example atoms that are not currently used */
export const spatialAggregateAtom = atomWithCustomStorage<ToggleOptions>({
  key: 'country-mode',
  initialValue: ToggleOptions.OFF,
  options: {
    syncWithUrl: true,
    syncWithLocalStorage: true,
  },
});

export const solarLayerAtom = atomWithCustomStorage<ToggleOptions>({
  key: 'solar',
  initialValue: ToggleOptions.OFF,
  options: {
    syncWithUrl: true,
    syncWithLocalStorage: true,
  },
});

export const windLayerAtom = atomWithCustomStorage<ToggleOptions>({
  key: 'wind',
  initialValue: ToggleOptions.OFF,
  options: {
    syncWithUrl: true,
    syncWithLocalStorage: true,
  },
});

export const themeAtom = atomWithStorage<ThemeOptions>('theme', ThemeOptions.LIGHT);

export const isLeftPanelOpenAtom = atomWithStorage(
  'is-left-panel-open',
  false,
  createJSONStorage(() => sessionStorage)
);
