import MapControls from 'features/map-controls/MapControls';
import Map from './Map';
import MapTooltip from './MapTooltip';

export default function MapWrapper() {
  return (
    <>
      <MapTooltip />
      <Map />
      <MapControls />
    </>
  );
}
