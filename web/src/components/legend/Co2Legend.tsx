import { useCo2ColorScale } from 'hooks/theme';
import { memo, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import { CarbonUnits } from 'utils/units';

import HorizontalColorbar from './ColorBar';
import { LegendItem } from './LegendItem';

function Co2Legend(): ReactElement {
  const { t } = useTranslation();
  const co2ColorScale = useCo2ColorScale();
  return (
    <LegendItem
      label={t('legends.carbonintensity')}
      unit={CarbonUnits.GRAMS_CO2EQ_PER_KILOWATT_HOUR}
    >
      <HorizontalColorbar colorScale={co2ColorScale} ticksCount={6} id={'co2'} />
    </LegendItem>
  );
}

export default memo(Co2Legend);
