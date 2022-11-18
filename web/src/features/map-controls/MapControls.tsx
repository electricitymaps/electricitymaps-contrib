import type { ReactElement } from 'react';
import ConsumptionProductionToggle from './ConsumptionProductionToggle';
import SpatialAggregatesToggle from './SpatialAggregatesToggle';

interface MapControlsProperties {}

export default function MapControls(properties: MapControlsProperties): ReactElement {
  return (
    <div className="z-1000 absolute right-10  top-20">
      <ConsumptionProductionToggle />
      <div className="mb-1"></div>
      <SpatialAggregatesToggle />
    </div>
  );
}
