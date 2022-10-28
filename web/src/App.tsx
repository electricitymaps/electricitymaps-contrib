import LoadingOrError from 'components/LoadingOrError';
import type { ReactElement } from 'react';
import { lazy, Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';

const Gallery = lazy(async () => import('features/boilerplate/Gallery'));
const Details = lazy(async () => import('features/boilerplate/Details'));
const Map = lazy(async () => import('features/map'));
const ZonePanel = lazy(async () => import('features/zone-details/ZonePanel'));

export default function App(): ReactElement {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingOrError />}>
        <Routes>
          <Route path="/" element={<Gallery />} />
          <Route path="/map" element={<Map />} />
          <Route path="/zone/:zoneId" element={<ZonePanel />} />
          <Route path=":fruitName" element={<Details />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
