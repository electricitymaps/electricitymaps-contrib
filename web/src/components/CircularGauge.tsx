import { Label, Pie, PieChart } from 'recharts';
import TooltipWrapper from './tooltips/TooltipWrapper';

const PIE_START_ANGLE = 90;

export interface CircularGaugeProps {
  ratio: number;
  name: string;
  tooltipContent?: string | JSX.Element;
  testId?: string;
}

export function CircularGauge({
  ratio,
  name,
  tooltipContent,
  testId,
}: CircularGaugeProps) {
  // TODO: To improve performance, the background pie does not need to rerender on percentage change
  const data = [{ value: ratio }];
  const percentageAsAngle = ratio * 360;
  const endAngle = PIE_START_ANGLE - percentageAsAngle;

  return (
    <div className="flex flex-col items-center">
      <TooltipWrapper
        side="right"
        tooltipContent={tooltipContent}
        tooltipClassName="max-w-44"
      >
        {/* Div required to ensure Tooltip is rendered in right place */}
        <div data-test-id={testId}>
          <PieChart
            width={65}
            height={65}
            margin={{ top: 0, left: 0, right: 0, bottom: 0 }}
          >
            <Pie
              innerRadius="80%"
              outerRadius="100%"
              startAngle={90}
              endAngle={-360}
              paddingAngle={0}
              dataKey="value"
              data={[{ value: 100 }]}
              className="fill-gray-200/60 dark:fill-gray-600/50"
              isAnimationActive={false}
              strokeWidth={0}
            >
              <Label
                className="select-none fill-gray-900 text-[1rem] font-bold dark:fill-gray-300"
                position="center"
                offset={0}
                formatter={(value: number) =>
                  !Number.isNaN(value) ? `${Math.round(value * 100)}%` : '?%'
                }
                value={ratio}
              />
            </Pie>
            <Pie
              data={data}
              innerRadius="80%"
              outerRadius="100%"
              startAngle={90}
              endAngle={endAngle}
              fill="#3C764A"
              paddingAngle={0}
              dataKey="value"
              animationDuration={500}
              animationBegin={0}
              strokeWidth={0}
            />
          </PieChart>
        </div>
      </TooltipWrapper>
      <p className="mt-2 text-center text-sm text-gray-900 dark:text-gray-300">{name}</p>
    </div>
  );
}
