import { useCo2ColorScale } from 'hooks/theme';
import type { ReactElement } from 'react';
import { useTranslation } from 'translation/translation';
import HorizontalColorbar from './ColorBar';

function LegendItem({
  isEnabled,
  label,
  unit,
  children,
}: {
  isEnabled: boolean;
  label: string;
  unit: string;
  children: ReactElement;
}) {
  return !isEnabled ? null : (
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
      <LegendItem label={__('legends.carbonintensity')} unit="gCO₂eq/kWh" isEnabled>
        <HorizontalColorbar colorScale={co2ColorScale} ticksCount={5} />
      </LegendItem>
    </div>
  );
}
