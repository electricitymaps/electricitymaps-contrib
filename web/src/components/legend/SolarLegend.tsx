import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';

import { solarColor } from '../../features/weather-layers/solar/utils';
import HorizontalColorbar from './ColorBar';
import { LegendItem } from './LegendItem';

export default function SolarLegend(): ReactElement {
  const { t } = useTranslation();
  return (
    <LegendItem label={t('legends.solarpotential')} unit="W/m²">
      <HorizontalColorbar colorScale={solarColor} id="solar" ticksCount={5} />
    </LegendItem>
  );
}
