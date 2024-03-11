import { ElectricityModeType } from 'types';
import { modeColor } from 'utils/constants';

import { LABEL_MAX_WIDTH, PADDING_Y } from './constants';
import ProductionSourceIcon from './ProductionsSourceIcons';

export default function ProductionSourceLegend({
  electricityType,
}: {
  electricityType: ElectricityModeType;
}) {
  return (
    <g className="pointer-events-none">
      <rect
        transform={`translate(${LABEL_MAX_WIDTH - 1.5 * PADDING_Y - 10}, 0)`}
        fill={modeColor[electricityType as ElectricityModeType]}
        width={14}
        height={14}
        rx={2}
      />
      <g
        transform={`translate(${LABEL_MAX_WIDTH - 1.5 * PADDING_Y - 7}, 3)`}
        width={14}
        height={8}
      >
        <ProductionSourceIcon source={electricityType} />
      </g>
    </g>
  );
}
