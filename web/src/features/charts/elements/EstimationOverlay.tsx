import { ZoneDetail } from 'types';

interface EstimationOverlayProps {
  width: number;
  height: number;
  zoneDetail?: ZoneDetail;
}

/**
 * A component that renders a semi-transparent overlay when data has an estimation method.
 * Used to indicate data that is estimated rather than measured directly.
 */
function EstimationOverlay({ width, height, zoneDetail }: EstimationOverlayProps) {
  if (!zoneDetail?.estimationMethod) {
    return null;
  }

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: `${width}px`,
        height: `${height}px`,
        backgroundColor: 'rgba(82, 82, 82, 0.1)',
        pointerEvents: 'none',
      }}
      aria-label="Estimated data overlay"
    />
  );
}

export default EstimationOverlay;
