import { ElectricityModeType } from 'types';
import { modeColor } from 'utils/constants';

import { iconHeight,LABEL_MAX_WIDTH, PADDING_Y } from './constants';
import { getIconPaddingFromIcon } from './utils';

export default function ProductionSourceLegend({
  electricityType,
}: {
  electricityType: ElectricityModeType;
}) {
  return (
    <g>
      <rect
        transform={`translate(${LABEL_MAX_WIDTH - 1.5 * PADDING_Y - 10}, 0)`}
        fill={modeColor[electricityType as ElectricityModeType]}
        width={14}
        height={14}
        rx={2}
      />
      <image
        transform={`translate(${
          LABEL_MAX_WIDTH - 1.5 * PADDING_Y - 10
        }, ${getIconPaddingFromIcon(electricityType)})`}
        width={14}
        height={iconHeight[electricityType as ElectricityModeType]}
        xlinkHref={`/images/production-source/${electricityType}.svg`}
      />
    </g>
  );
}
