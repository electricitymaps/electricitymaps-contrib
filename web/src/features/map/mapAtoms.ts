import { atom } from 'jotai';
import { HoveredZone } from './mapTypes';

export const loadingMapAtom = atom(true);

export const mousePositionAtom = atom({
  x: 0,
  y: 0,
});

export const hoveredZoneAtom = atom<HoveredZone | null>(null);

export const mapMovingAtom = atom(false);
