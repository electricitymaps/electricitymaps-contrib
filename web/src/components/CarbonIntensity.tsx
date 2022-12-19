import { useCo2ColorScale } from 'hooks/theme';

export function CarbonIntensityDisplayWithSquare({
  co2Intensity,
}: {
  co2Intensity: number;
}) {
  const co2ColorScale = useCo2ColorScale();

  return (
    <>
      <div
        style={{
          backgroundColor: co2ColorScale(co2Intensity),
          width: '8px',
          height: '8px',
        }}
      />{' '}
      <CarbonIntensityDisplay co2Intensity={co2Intensity} />
    </>
  );
}

export function CarbonIntensityDisplay({ co2Intensity }: { co2Intensity: number }) {
  return (
    <p>
      <b>{Math.round(co2Intensity) || '?'}</b> gCO₂eq/kWh
    </p>
  );
}
