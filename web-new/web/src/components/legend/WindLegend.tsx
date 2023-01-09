import type { ReactElement } from 'react';
import { useTranslation } from 'translation/translation';
import HorizontalColorbar from './ColorBar';
import { windColor } from 'features/weather-layers/wind-layer/scales';

function LegendItem({
  label,
  unit,
  children,
}: {
  label: string;
  unit: string | ReactElement;
  children: ReactElement;
}) {
  return (
    <div className="text-center">
      <p className="py-1  text-base">
        {label} <small>({unit})</small>
      </p>
      {children}
    </div>
  );
}

export default function WindLegend(): ReactElement {
  const { __ } = useTranslation();
  return (
    <div>
      <LegendItem label={__('legends.windpotential')} unit="m/s">
        <HorizontalColorbar colorScale={windColor} id="wind" ticksCount={6} />
      </LegendItem>
    </div>
  );
}
