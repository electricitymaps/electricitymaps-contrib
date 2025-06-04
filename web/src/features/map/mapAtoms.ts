import { atom } from 'jotai';

import { FeatureId } from './mapTypes';

export const loadingMapAtom = atom(true);

export const mousePositionAtom = atom<{ x: number; y: number }>({ x: 0, y: 0 });

export const hoveredZoneAtom = atom<{ featureId: FeatureId; zoneId: string } | null>(
  null
);

export const mapMovingAtom = atom(false);

export const selectedSolarAssetAtom = atom<{
  id: FeatureId;
  properties: Record<string, string | number | null>;
} | null>(null);

export const mapZoomAtom = atom<number>(2.5);

export interface HoveredSolarAssetInfo {
  properties: Record<string, string | number>;
  x: number;
  y: number;
}
export const hoveredSolarAssetInfoAtom = atom<HoveredSolarAssetInfo | null>(null);
