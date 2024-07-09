import { extent } from 'd3-array';
import { ScaleLinear, scaleLinear } from 'd3-scale';
import { TFunction } from 'i18next';
import { CarbonUnits } from 'utils/units';

import { spreadOverDomain } from './utils';

function Co2LegendRounded({
  colorScale,
  ticksCount = 5,
  t,
}: {
  colorScale: ScaleLinear<string, string, string>;
  ticksCount?: number;
  t: TFunction<'translation', undefined>;
}) {
  const linearScale = scaleLinear().domain(
    extent(colorScale.domain()) as unknown as [number, number]
  );

  return (
    <div className="mb-5 mt-2">
      <div className="mb-1 text-xs font-medium text-neutral-600 dark:text-gray-300">
        {t('legends.carbonintensity')} ({CarbonUnits.GRAMS_CO2EQ_PER_WATT_HOUR})
      </div>
      <svg className="flex h-3 w-full flex-col overflow-visible">
        <g transform={`translate(8,0)`}>
          <linearGradient id={`co2-gradient`} x2="100%">
            {spreadOverDomain(colorScale, 10).map((value, index) => (
              <stop key={value} offset={index / 9} stopColor={colorScale(value)} />
            ))}
          </linearGradient>
          <rect
            fill={`url(#co2-gradient)`}
            width="100%"
            height={8}
            rx={5}
            transform="translate(-10,0)"
          />
        </g>
      </svg>
      <div className="flex flex-row justify-between pr-0.5">
        {spreadOverDomain(linearScale, ticksCount).map((t) => (
          <div
            key={`colorbar-tick-${t}`}
            className="text-xs font-medium text-neutral-600 dark:text-gray-300"
          >
            {Math.round(t)}
          </div>
        ))}
      </div>
    </div>
  );
}

export default Co2LegendRounded;
