import { Annotation, Label } from '@visx/annotation';
import { Group } from '@visx/group';
import { Arc } from '@visx/shape';
import type { DatumObject } from '@visx/shape/lib/types';
import { memo } from 'react';

import TooltipWrapper from './tooltips/TooltipWrapper';

const PIE_START_ANGLE = 0;

export interface CircularGaugeProps {
  ratio: number;
  name: string;
  tooltipContent?: string | JSX.Element;
  testId?: string;
}

const BackgroundArc = memo(function BackgroundArc({ radius }: { radius: number }) {
  return (
    <Arc
      innerRadius={radius * 0.8}
      outerRadius={radius}
      startAngle={90}
      endAngle={-360}
      data={{ value: 100 }}
      className="fill-gray-200/60 dark:fill-gray-600/50"
      strokeWidth={0}
    />
  );
});

export function CircularGauge({
  ratio,
  name,
  tooltipContent,
  testId,
}: CircularGaugeProps) {
  const data: DatumObject = { value: ratio };
  const percentageAsAngle = ratio * 360;
  const endAngle = PIE_START_ANGLE + (percentageAsAngle * Math.PI) / 180;
  const height = 65;
  const width = 65;
  const radius = Math.min(width, height) / 2;
  const centerY = height / 2;
  const centerX = width / 2;

  return (
    <div className="flex flex-col items-center">
      <TooltipWrapper
        side="right"
        tooltipContent={tooltipContent}
        tooltipClassName="max-w-44"
      >
        {/* Div required to ensure Tooltip is rendered in right place */}
        <div data-test-id={testId}>
          <svg height={height} width={width}>
            <Group top={centerY} left={centerX}>
              <BackgroundArc radius={radius} />
              <Arc
                height={height}
                width={width}
                innerRadius={radius * 0.8}
                outerRadius={radius}
                data={data}
                startAngle={PIE_START_ANGLE}
                endAngle={endAngle}
                strokeWidth={1}
                fill="#3C764A"
              />
              <Annotation>
                {/* Consider memoizing this */}
                <Label
                  verticalAnchor="middle"
                  horizontalAnchor="middle"
                  backgroundFill="transparent"
                  fontColor="currentColor"
                  showAnchorLine={false}
                  title={Number.isNaN(ratio) ? '?%' : `${Math.round(ratio * 100)}%`}
                />
              </Annotation>
            </Group>
          </svg>
        </div>
      </TooltipWrapper>
      <p className="mt-2 text-center text-xs font-semibold text-neutral-600 dark:text-neutral-400">
        {name}
      </p>
    </div>
  );
}
