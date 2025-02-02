import { usePriceColorScale } from 'hooks/theme';
import { memo, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';

import HorizontalColorbar from './ColorBar';
import { LegendItem } from './LegendItem';

function PriceLegend(): ReactElement {
  const { t } = useTranslation();
  const priceColorScale = usePriceColorScale();
  return (
    <LegendItem label={t('legends.price')} unit={`€`}>
      <HorizontalColorbar colorScale={priceColorScale} ticksCount={6} id={'price'} />
    </LegendItem>
  );
}

export default memo(PriceLegend);
