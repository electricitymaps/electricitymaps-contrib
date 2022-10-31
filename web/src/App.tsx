import LoadingOrError from 'components/LoadingOrError';
import LeftPanel from 'features/panels/LeftPanel';
import type { ReactElement } from 'react';
import { lazy, Suspense } from 'react';

const Map = lazy(async () => import('features/map/Map'));

export default function App(): ReactElement {
  return (
    <Suspense fallback={<LoadingOrError />}>
      <LeftPanel />
      <Map />
    </Suspense>
  );
}
