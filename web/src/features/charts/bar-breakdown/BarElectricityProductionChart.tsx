import { Group } from '@visx/group';
import { ScaleLinear } from 'd3-scale';
import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import { ElectricityModeType } from 'types';
import { modeColor } from 'utils/constants';

import { AXIS_LEGEND_PADDING } from './constants';
import Axis, { FormatTick } from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import { ProductionSourceRow } from './elements/Row';
import { getElectricityProductionValue, ProductionDataType } from './utils';

function BarElectricityProductionChart({
  powerScale,
  height,
  formatTick,
  productionY,
  productionData,
  width,
  onProductionRowMouseOver,
  onProductionRowMouseOut,
  isMobile,
}: {
  powerScale: ScaleLinear<number, number, never>;
  height: number;
  formatTick: FormatTick;
  productionY: number;
  productionData: ProductionDataType[];
  width: number;
  onProductionRowMouseOver: (
    rowKey: ElectricityModeType,
    event: React.MouseEvent<SVGPathElement, MouseEvent>
  ) => void;
  onProductionRowMouseOut: () => void;
  isMobile: boolean;
}) {
  const { t } = useTranslation();
  return (
    <svg className="w-full overflow-visible" height={height + AXIS_LEGEND_PADDING}>
      <Axis
        formatTick={formatTick}
        height={height}
        scale={powerScale}
        axisLegendTextLeft={t('country-panel.graph-legends.stored')}
        axisLegendTextRight={t('country-panel.graph-legends.produced')}
      />
      <Group top={productionY}>
        {productionData.map((d, index) => (
          <ProductionSourceRow
            key={d.mode}
            index={index}
            productionMode={d.mode}
            width={width}
            scale={powerScale}
            value={getElectricityProductionValue(d)}
            onMouseOver={(event) => onProductionRowMouseOver(d.mode, event)}
            onMouseOut={onProductionRowMouseOut}
            isMobile={isMobile}
          >
            <HorizontalBar
              className="text-black/10 dark:text-white/10"
              fill="currentColor"
              range={d.isStorage ? [-(d.capacity || 0), d.capacity] : [0, d.capacity]}
              scale={powerScale}
            />
            <HorizontalBar
              className="production"
              fill={modeColor[d.mode]}
              range={[0, getElectricityProductionValue(d)]}
              scale={powerScale}
            />
          </ProductionSourceRow>
        ))}
      </Group>
    </svg>
  );
}

export default memo(BarElectricityProductionChart);
