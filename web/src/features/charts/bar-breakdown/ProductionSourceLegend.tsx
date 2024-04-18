import { ElectricityModeType } from 'types';
import { modeColor } from 'utils/constants';

import ProductionSourceIcon from './ProductionsSourceIcons';

export default function ProductionSourceLegend({
  electricityType,
}: {
  electricityType: ElectricityModeType;
}) {
  return (
    <svg width={14} height={14}>
      <g className="pointer-events-none">
        <rect
          fill={modeColor[electricityType as ElectricityModeType]}
          width={14}
          height={14}
          rx={2}
        />
        <g transform={`translate(3, 3)`} width={14} height={8}>
          <ProductionSourceIcon source={electricityType} />
        </g>
      </g>
    </svg>
  );
}
