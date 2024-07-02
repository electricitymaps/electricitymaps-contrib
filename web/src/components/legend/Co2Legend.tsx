import { useCo2ColorScale } from 'hooks/theme';
import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import { CarbonUnits } from 'utils/units';

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
      <p className="py-1 font-poppins">
        {label} <small>({unit})</small>
      </p>
      {children}
    </div>
  );
}

export default function Co2Legend(): ReactElement {
  const { t } = useTranslation();
  const co2ColorScale = useCo2ColorScale();
  return (
    <div>
      <LegendItem
        label={t('legends.carbonintensity')}
        unit={CarbonUnits.GRAMS_CO2EQ_PER_WATT_HOUR}
      >
        <HorizontalColorbar colorScale={co2ColorScale} ticksCount={6} id={'co2'} />
      </LegendItem>
    </div>
  );
}
