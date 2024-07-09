import { TFunction } from 'i18next';
import { FaArrowLeft, FaArrowRight } from 'react-icons/fa';

import { X_AXIS_HEIGHT } from '../constants';

export default function ExchangeLegend({ height, t }: { height: number; t: TFunction }) {
  return (
    <>
      <line
        stroke="currentColor"
        strokeWidth={1}
        shapeRendering={'auto'}
        y1={height - X_AXIS_HEIGHT}
        y2={height - X_AXIS_HEIGHT + 15}
      />
      <text
        fill="rgba(115, 115, 115, 1)"
        fontSize={'0.7rem'}
        y={height - X_AXIS_HEIGHT + 10}
        x={-40}
        dy="0"
      >
        {t('country-panel.graph-legends.exported')}
      </text>
      <FaArrowLeft
        className="text-neutral-300 dark:text-gray-700"
        x={-15}
        y={height - X_AXIS_HEIGHT + 2}
      />
      <FaArrowRight
        className="text-neutral-300 dark:text-gray-700"
        x={5}
        y={height - X_AXIS_HEIGHT + 2}
      />
      <text
        fill="rgba(115, 115, 115, 1)"
        fontSize={'0.7rem'}
        y={height - X_AXIS_HEIGHT + 10}
        x={40}
        dy="0"
      >
        {t('country-panel.graph-legends.imported')}
      </text>
    </>
  );
}
