import type { ReactElement } from 'react';
import { useTranslation } from 'translation/translation';
import HorizontalColorbar from './ColorBar';
import { solarColor } from '../../features/weather-layers/solar/utils';

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

export default function SolarLegend(): ReactElement {
  const { __ } = useTranslation();
  return (
    <div>
      <LegendItem label={__('legends.solarpotential')} unit="W/m²">
        <HorizontalColorbar colorScale={solarColor} id="solar" ticksCount={5} />
      </LegendItem>
    </div>
  );
}
