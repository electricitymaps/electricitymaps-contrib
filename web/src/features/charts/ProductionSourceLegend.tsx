import { Group } from '@visx/group';
import { memo } from 'react';
import { ElectricityModeType } from 'types';
import { DEFAULT_ICON_SIZE, modeColor } from 'utils/constants';

import ProductionSourceIcon from './ProductionsSourceIcons';

function ProductionSourceLegend({
  electricityType,
}: {
  electricityType: ElectricityModeType;
}) {
  return (
    <svg
      width={DEFAULT_ICON_SIZE}
      height={DEFAULT_ICON_SIZE}
      className="pointer-events-none"
    >
      <rect
        fill={modeColor[electricityType as ElectricityModeType]}
        width={DEFAULT_ICON_SIZE}
        height={DEFAULT_ICON_SIZE}
        rx={2}
      />
      <Group top={3} left={3} width={DEFAULT_ICON_SIZE} height={DEFAULT_ICON_SIZE}>
        <ProductionSourceIcon source={electricityType} />
      </Group>
    </svg>
  );
}

export default memo(ProductionSourceLegend);
