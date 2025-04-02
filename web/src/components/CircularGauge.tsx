import { animated, useSpring } from '@react-spring/web';
import { Group } from '@visx/group';
import { Arc } from '@visx/shape';
import { Text } from '@visx/text';
import { memo } from 'react';

import InfoIconWithPadding from './InfoIconWithPadding';
import LabelTooltip from './tooltips/LabelTooltip';
import TooltipWrapper from './tooltips/TooltipWrapper';

const FULL_CIRCLE = 360;
const HALF_CIRCLE = FULL_CIRCLE / 2;
const PIE_PADDING = 30;

const degreesToRadians = (degrees: number) => (degrees * Math.PI) / HALF_CIRCLE;

/** The start angle of the pie chart, calculated from the `PIE_PADDING` and then adjusted for rotation */
const PIE_START_ANGLE = degreesToRadians(PIE_PADDING + HALF_CIRCLE);
/** The end angle of the pie chart, calculated from the `PIE_PADDING` and then adjusted for rotation */
const PIE_END_ANGLE = degreesToRadians(FULL_CIRCLE - PIE_PADDING + HALF_CIRCLE);

const calculateEndAngle = (ratio: number) =>
  PIE_START_ANGLE + degreesToRadians(ratio * (FULL_CIRCLE - PIE_PADDING * 2));

export interface CircularGaugeProps {
  ratio: number;
  name: string;
  tooltipContent?: string | JSX.Element;
  testId?: string;
}

const BackgroundArc = memo(function BackgroundArc({ radius }: { radius: number }) {
  return (
    <Arc
      outerRadius={radius}
      innerRadius={radius * 0.8}
      startAngle={PIE_START_ANGLE}
      endAngle={PIE_END_ANGLE}
      className="fill-neutral-600/15 dark:fill-neutral-600/50"
      cornerRadius={radius}
    />
  );
});

const AnimatedArc = animated(Arc);

// Memoized to avoid unnecessary re-renders due to floating point precision issues
const SpringAnimatedArc = memo(function SpringAnimatedArc({
  radius,
  ratio,
}: {
  radius: number;
  ratio: number;
}) {
  const [spring] = useSpring(
    {
      to: { ratio: Number.isFinite(ratio) ? ratio : 0 },
      from: { ratio: 0 },
    },
    [ratio]
  );

  return (
    <AnimatedArc
      innerRadius={radius * 0.8}
      outerRadius={radius}
      startAngle={PIE_START_ANGLE}
      endAngle={spring.ratio.to((ratio) => calculateEndAngle(ratio))}
      cornerRadius={radius}
      className="fill-brand-green dark:fill-brand-green-dark"
    />
  );
});

function CircularGauge({ ratio, name, testId, tooltipContent }: CircularGaugeProps) {
  const height = 80;
  const width = 80;
  const radius = Math.min(width, height) / 2;
  const centerY = height / 2;
  const centerX = width / 2;

  return (
    <div className="flex flex-col items-center gap-2">
      <TooltipWrapper
        tooltipContent={<LabelTooltip>{tooltipContent}</LabelTooltip>}
        side="bottom"
        sideOffset={8}
      >
        <div data-testid={testId} className="relative flex flex-col items-center">
          <svg height={height} width={width}>
            <Group top={centerY} left={centerX} height={height} width={width}>
              <BackgroundArc radius={radius} />
              <SpringAnimatedArc radius={radius} ratio={ratio} />
              <Text
                verticalAnchor="middle"
                textAnchor="middle"
                fill="currentColor"
                className="text-base font-semibold"
              >
                {Number.isFinite(ratio) ? `${Math.round(ratio * 100)}%` : '?%'}
              </Text>
            </Group>
          </svg>
          {tooltipContent && <InfoIconWithPadding />}
        </div>
      </TooltipWrapper>
      <p className="text-xs font-semibold text-neutral-600 dark:text-neutral-400">
        {name}
      </p>
    </div>
  );
}

export default memo(CircularGauge);
