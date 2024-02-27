import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';

import { solarColor } from '../../features/weather-layers/solar/utils';
import HorizontalColorbar from './ColorBar';

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
  const { t } = useTranslation();
  return (
    <div>
      <LegendItem label={t('legends.solarpotential')} unit="W/m²">
        <HorizontalColorbar colorScale={solarColor} id="solar" ticksCount={5} />
      </LegendItem>
    </div>
  );
}
