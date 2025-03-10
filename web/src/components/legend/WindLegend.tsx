import { windColor } from 'features/weather-layers/wind-layer/scales';
import { memo, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';

import HorizontalColorbar from './ColorBar';
import { LegendItem } from './LegendItem';

function WindLegend(): ReactElement {
  const { t } = useTranslation();
  return (
    <LegendItem label={t('legends.windpotential')} unit="m/s">
      <HorizontalColorbar colorScale={windColor} id="wind" ticksCount={6} />
    </LegendItem>
  );
}

export default memo(WindLegend);
