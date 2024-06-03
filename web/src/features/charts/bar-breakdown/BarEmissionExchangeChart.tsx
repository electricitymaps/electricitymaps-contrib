import { CountryFlag } from 'components/Flag';
import { ScaleLinear } from 'd3-scale';
import { ZoneDetail, ZoneKey } from 'types';

import Axis from './elements/Axis';
import HorizontalBar from './elements/HorizontalBar';
import Row from './elements/Row';
import { ExchangeDataType } from './utils';

export default function BarEmissionExchangeChart({
  height,
  exchangeData,
  width,
  co2Scale,
  data,
  formatTick,
  onExchangeRowMouseOut,
  onExchangeRowMouseOver,
}: {
  height: number;
  onExchangeRowMouseOver: (
    rowKey: ZoneKey,
    data: ZoneDetail,
    event: React.MouseEvent<SVGPathElement, MouseEvent>
  ) => void;
  onExchangeRowMouseOut: () => void;
  exchangeData: ExchangeDataType[];
  data: ZoneDetail;
  width: number;
  co2Scale: ScaleLinear<number, number, never>;
  formatTick: (value: number) => string;
}) {
  return (
    <svg className="w-full overflow-visible" height={height}>
      <Axis formatTick={formatTick} height={height} scale={co2Scale} />
      <g transform={`translate(0, ${20})`}>
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
  );
}
