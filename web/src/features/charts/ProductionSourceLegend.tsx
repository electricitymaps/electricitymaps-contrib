import { ElectricityModeType } from 'types';
import { modeColor } from 'utils/constants';

import ProductionSourceIcon from './ProductionsSourceIcons';

export default function ProductionSourceLegend({
  electricityType,
}: {
  electricityType: ElectricityModeType;
}) {
  return (
    <svg width={16} height={16}>
      <g className="pointer-events-none">
        <rect
          fill={modeColor[electricityType as ElectricityModeType]}
          width={16}
          height={16}
          rx={2}
        />
        <g transform={`translate(3, 3)`} width={16} height={16}>
          <ProductionSourceIcon source={electricityType} />
        </g>
      </g>
    </svg>
  );
}
