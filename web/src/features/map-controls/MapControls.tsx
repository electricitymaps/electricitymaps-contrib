import { Sun, Wind } from 'lucide-react';
import { lazy, Suspense } from 'react';
import {
  solarLayerAtom,
  solarLayerLoadingAtom,
  windLayerAtom,
  windLayerLoadingAtom,
} from 'utils/state/atoms';

import LayersModal from '../modals/LayersModal';
import MapButtons from './MapButtons';

const SettingsModal = lazy(() => import('features/modals/SettingsModal'));

export const weatherButtonMap = {
  wind: {
    icon: Wind,
    iconSize: 20,
    enabledAtom: windLayerAtom,
    loadingAtom: windLayerLoadingAtom,
  },
  solar: {
    icon: Sun,
    iconSize: 20,
    enabledAtom: solarLayerAtom,
    loadingAtom: solarLayerLoadingAtom,
  },
};

export default function MapControls() {
  return (
    <>
      <MapButtons />
      <Suspense>
        <SettingsModal />
      </Suspense>
      <Suspense>
        <LayersModal />
      </Suspense>
    </>
  );
}
