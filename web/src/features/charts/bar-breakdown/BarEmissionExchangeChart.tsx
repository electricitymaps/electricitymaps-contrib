import { Group } from '@visx/group';
import { ScaleLinear } from 'd3-scale';
import { useTranslation } from 'react-i18next';
import { ZoneKey } from 'types';
import { useIsMobile } from 'utils/styling';

import { EXCHANGE_PADDING } from './constants';
import Axis, { FormatTick } from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import { ExchangeRow } from './elements/Row';
import { ExchangeDataType } from './utils';

export default function BarEmissionExchangeChart({
  height,
  width,
  exchangeData,
  co2Scale,
  formatTick,
  onExchangeRowMouseOut,
  onExchangeRowMouseOver,
}: {
  height: number;
  width: number;
  exchangeData: ExchangeDataType[];
  co2Scale: ScaleLinear<number, number, never>;
  formatTick: FormatTick;
  onExchangeRowMouseOut: () => void;
  onExchangeRowMouseOver: (
    rowKey: ZoneKey,
    event: React.MouseEvent<SVGPathElement, MouseEvent>
  ) => void;
}) {
  const { t } = useTranslation();
  const isMobile = useIsMobile();
  if (!exchangeData || exchangeData.length === 0) {
    return null;
  }
  return (
    <div className="pb-4 pt-2">
      <svg className="w-full overflow-visible" height={height}>
        <Axis
          formatTick={formatTick}
          height={height}
          scale={co2Scale}
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
              capacity={d.exchangeCapacityRange}
              value={d.exchange}
              onMouseOver={(event) => onExchangeRowMouseOver(d.zoneKey, event)}
              onMouseOut={onExchangeRowMouseOut}
              isMobile={isMobile}
            >
              <HorizontalBar
                className="exchange"
                fill={'gray'}
                range={[0, d.gCo2eq]}
                scale={co2Scale}
              />
            </ExchangeRow>
          ))}
        </Group>
      </svg>
    </div>
  );
}
