import { Group } from '@visx/group';
import HorizontalColorbar from 'components/legend/ColorBar';
import { ScaleLinear } from 'd3-scale';
import { useTranslation } from 'react-i18next';
import { ZoneKey } from 'types';
import { CarbonUnits } from 'utils/units';

import { EXCHANGE_PADDING } from './constants';
import Axis, { FormatTick } from './elements/Axis';
import CapacityLegend from './elements/CapacityLegend';
import HorizontalBar from './elements/HorizontalBar';
import { ExchangeRow } from './elements/Row';
import { ExchangeDataType } from './utils';

export default function BarElectricityExchangeChart({
  height,
  width,
  exchangeData,
  powerScale,
  co2ColorScale,
  graphUnit,
  formatTick,
  onExchangeRowMouseOut,
  onExchangeRowMouseOver,
}: {
  height: number;
  width: number;
  exchangeData: ExchangeDataType[];
  powerScale: ScaleLinear<number, number, never>;
  co2ColorScale: ScaleLinear<string, string, string>;
  graphUnit: string | undefined;
  formatTick: FormatTick;
  onExchangeRowMouseOut: () => void;
  onExchangeRowMouseOver: (
    rowKey: ZoneKey,
    event: React.MouseEvent<SVGPathElement, MouseEvent>
  ) => void;
}) {
  const { t } = useTranslation();

  if (!exchangeData || exchangeData.length === 0) {
    return null;
  }

  return (
    <>
      <CapacityLegend
        text={t('country-panel.graph-legends.exchange-capacity')}
        unit={graphUnit}
      />
      <svg className="w-full overflow-visible" height={height}>
        <Axis
          formatTick={formatTick}
          height={height}
          scale={powerScale}
          axisLegendTextLeft={t('country-panel.graph-legends.exported')}
          axisLegendTextRight={t('country-panel.graph-legends.imported')}
        />
        <Group top={EXCHANGE_PADDING}>
          {exchangeData.map((d, index) => (
            <ExchangeRow
              key={d.zoneKey}
              index={index}
              zoneKey={d.zoneKey}
              width={width}
              scale={powerScale}
              value={d.exchange}
              onMouseOver={(event) => onExchangeRowMouseOver(d.zoneKey, event)}
              onMouseOut={onExchangeRowMouseOut}
              isMobile={false}
            >
              <HorizontalBar
                className="text-black/10 dark:text-white/10"
                fill="currentColor"
                range={d.exchangeCapacityRange}
                scale={powerScale}
              />
              <HorizontalBar
                className="exchange"
                fill={co2ColorScale(d.gCo2eqPerkWh ?? Number.NaN)}
                range={[0, d.exchange]}
                scale={powerScale}
              />
            </ExchangeRow>
          ))}
        </Group>
      </svg>
      <div className="pb-2 pt-6">
        <div className="mb-1 text-xs font-medium text-neutral-600 dark:text-neutral-300">
          {t('legends.carbonintensity')} ({CarbonUnits.GRAMS_CO2EQ_PER_KILOWATT_HOUR})
        </div>
        <HorizontalColorbar colorScale={co2ColorScale} ticksCount={6} id={'co2'} />
      </div>
    </>
  );
}
