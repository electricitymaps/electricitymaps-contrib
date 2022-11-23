import LoadingOverlay from 'components/LoadingOverlay';
import ErrorBoundary from 'features/error-boundary/ErrorBoundary';
import Header from 'features/header/Header';
import MapControls from 'features/map-controls/MapControls';
import TimeController from 'features/time/TimeController';
import type { ReactElement } from 'react';
import { lazy, Suspense } from 'react';

const Map = lazy(async () => import('features/map/Map'));
const LeftPanel = lazy(async () => import('features/panels/LeftPanel'));

export default function App(): ReactElement {
  return (
    <Suspense fallback={<div />}>
      <main className="fixed flex h-screen w-screen flex-col">
        <Header />
        <div className="relative flex flex-auto items-stretch">
          <ErrorBoundary>
            <LoadingOverlay />
            <LeftPanel />
            <Map />
            <TimeController />
            <MapControls />
          </ErrorBoundary>
        </div>
      </main>
    </Suspense>
  );
}
