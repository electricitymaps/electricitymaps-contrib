import { useCo2ColorScale } from 'hooks/theme';
import type { ReactElement } from 'react';
import { useTranslation } from 'translation/translation';
import HorizontalColorbar from './ColorBar';

function LegendItem({
  label,
  unit,
  children,
}: {
  label: string;
  unit: string;
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

export default function Co2Legend(): ReactElement {
  const { __ } = useTranslation();
  const co2ColorScale = useCo2ColorScale();
  return (
    <div>
      <LegendItem label={__('legends.carbonintensity')} unit="gCO₂eq/kWh">
        <HorizontalColorbar colorScale={co2ColorScale} ticksCount={5} id={'co2'} />
      </LegendItem>
    </div>
  );
}
