import { CountryFlag } from 'components/Flag';
import { ScaleLinear } from 'd3-scale';
import { useTranslation } from 'react-i18next';
import { ZoneDetail, ZoneKey } from 'types';

import { EXCHANGE_PADDING } from './constants';
import Axis from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import Row from './elements/Row';
import { ExchangeDataType } from './utils';

export default function BarEmissionExchangeChart({
  height,
  width,
  data,
  exchangeData,
  co2Scale,
  formatTick,
  onExchangeRowMouseOut,
  onExchangeRowMouseOver,
}: {
  height: number;
  width: number;
  data: ZoneDetail;
  exchangeData: ExchangeDataType[];
  co2Scale: ScaleLinear<number, number, never>;
  formatTick: (value: number) => string;
  onExchangeRowMouseOut: () => void;
  onExchangeRowMouseOver: (
    rowKey: ZoneKey,
    data: ZoneDetail,
    event: React.MouseEvent<SVGPathElement, MouseEvent>
  ) => void;
}) {
  const { t } = useTranslation();

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
          axisLegendText={{
            left: t('country-panel.graph-legends.exported'),
            right: t('country-panel.graph-legends.imported'),
          }}
        />
        <g transform={`translate(0, ${EXCHANGE_PADDING})`}>
          {exchangeData.map((d, index) => (
            <Row
              key={d.zoneKey}
              index={index}
              label={d.zoneKey}
              width={width}
              scale={co2Scale}
              value={d.exchange}
              onMouseOver={(event) => onExchangeRowMouseOver(d.zoneKey, data, event)}
              onMouseOut={onExchangeRowMouseOut}
              isMobile={false}
            >
              <g transform={`translate(-2, 0)`}>
                <CountryFlag zoneId={d.zoneKey} className="pointer-events-none" />
              </g>
              <HorizontalBar
                className="exchange"
                fill={'gray'}
                range={[0, d.gCo2eq]}
                scale={co2Scale}
              />
            </Row>
          ))}
        </g>
      </svg>
    </div>
  );
}
