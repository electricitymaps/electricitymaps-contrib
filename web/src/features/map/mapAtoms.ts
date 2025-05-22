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
  properties: Record<string, any>;
} | null>(null);

export const mapZoomAtom = atom<number>(2.5); // Default initial zoom

export interface HoveredSolarAssetInfo {
  properties: Record<string, any>; // Using Record<string, any> for generic properties
  x: number;
  y: number;
}
export const hoveredSolarAssetInfoAtom = atom<HoveredSolarAssetInfo | null>(null);
