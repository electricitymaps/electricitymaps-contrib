/* eslint-disable jsx-a11y/mouse-events-have-key-events */
import React, {
  useRef,
  useMemo,
  useEffect,
  useState,
} from 'react';
import { connect, useSelector } from 'react-redux';
import { scaleLinear } from 'd3-scale';
import { max as d3Max, min as d3Min } from 'd3-array';
import { precisionPrefix, formatPrefix } from 'd3-format';
import { isArray, isFinite, noop } from 'lodash';

import { dispatch, dispatchApplication } from '../store';
import { useWidthObserver } from '../hooks/viewport';
import {
  useCurrentZoneData,
  useCurrentZoneExchangeKeys,
} from '../hooks/redux';
import { useCo2ColorScale } from '../hooks/theme';
import { getTooltipPosition } from '../helpers/graph';
import { modeOrder, modeColor, DEFAULT_FLAG_SIZE } from '../helpers/constants';
import { getProductionCo2Intensity, getExchangeCo2Intensity } from '../helpers/zonedata';
import { flagUri } from '../helpers/flags';
import { __ } from '../helpers/translation';

import CountryPanelProductionTooltip from './tooltips/countrypanelproductiontooltip';
import CountryPanelExchangeTooltip from './tooltips/countrypanelexchangetooltip';
import CountryTableOverlayIfNoData from './countrytableoverlayifnodata';

const LABEL_MAX_WIDTH = 102;
const TEXT_ADJUST_Y = 11;
const ROW_HEIGHT = 13;
const PADDING_Y = 7;
const PADDING_X = 5;
const RECT_OPACITY = 0.8;
const X_AXIS_HEIGHT = 15;
const SCALE_TICKS = 4;

const getProductionData = data => modeOrder.map((mode) => {
  const isStorage = mode.indexOf('storage') !== -1;
  const resource = mode.replace(' storage', '');

  // Power in MW
  const capacity = (data.capacity || {})[mode];
  const production = (data.production || {})[resource];
  const storage = (data.storage || {})[resource];

  // Production CO₂ intensity
  const gCo2eqPerkWh = getProductionCo2Intensity(mode, data);
  const gCo2eqPerHour = gCo2eqPerkWh * 1e3 * (isStorage ? storage : production);
  const tCo2eqPerMin = gCo2eqPerHour / 1e6 / 60.0;

  return {
    isStorage,
    storage,
    production,
    capacity,
    mode,
    tCo2eqPerMin,
  };
});

const getExchangeData = (data, exchangeKeys, electricityMixMode) => exchangeKeys.map((mode) => {
  // Power in MW
  const exchange = (data.exchange || {})[mode];
  const exchangeCapacityRange = (data.exchangeCapacities || {})[mode];

  // Exchange CO₂ intensity
  const gCo2eqPerkWh = getExchangeCo2Intensity(mode, data, electricityMixMode);
  const gCo2eqPerHour = gCo2eqPerkWh * 1e3 * exchange;
  const tCo2eqPerMin = gCo2eqPerHour / 1e6 / 60.0;

  return {
    exchange,
    exchangeCapacityRange,
    mode,
    gCo2eqPerkWh,
    tCo2eqPerMin,
  };
});

const getDataBlockPositions = (productionData, exchangeData) => {
  const productionHeight = productionData.length * (ROW_HEIGHT + PADDING_Y);
  const productionY = X_AXIS_HEIGHT + PADDING_Y;

  const exchangeFlagX = LABEL_MAX_WIDTH - 4.0 * PADDING_X - DEFAULT_FLAG_SIZE - d3Max(exchangeData, d => d.mode.length) * 8;
  const exchangeHeight = exchangeData.length * (ROW_HEIGHT + PADDING_Y);
  const exchangeY = productionY + productionHeight + ROW_HEIGHT + PADDING_Y;

  return {
    productionHeight,
    productionY,
    exchangeFlagX,
    exchangeHeight,
    exchangeY,
  };
};

const Axis = ({ formatTick, height, scale }) => (
  <g
    className="x axis"
    fill="none"
    fontSize="10"
    fontFamily="sans-serif"
    textAnchor="middle"
    transform={`translate(${scale.range()[0] + LABEL_MAX_WIDTH}, ${X_AXIS_HEIGHT})`}
  >
    <path className="domain" stroke="currentColor" d={`M${scale.range()[0] + 0.5},0.5H${scale.range()[1] + 0.5}`} />
    {scale.ticks(SCALE_TICKS).map(t => (
      <g
        key={t}
        className="tick"
        opacity="1"
        transform={`translate(${scale(t)}, 0)`}
      >
        <line stroke="currentColor" y2={height - X_AXIS_HEIGHT} />
        <text fill="currentColor" y="-3" dy="0">{formatTick(t)}</text>
      </g>
    ))}
  </g>
);

const Row = ({
  children,
  index,
  isMobile,
  label,
  onMouseOver,
  onMouseOut,
  width,
}) => {
  // Don't render if the width is not positive
  if (width <= 0) return null;

  return (
    <g className="row" transform={`translate(0, ${index * (ROW_HEIGHT + PADDING_Y)})`}>
      {/* Row background */}
      <rect
        y="-1"
        fill="transparent"
        width={width}
        height={ROW_HEIGHT + PADDING_Y}
        /* Support only click events in mobile mode, otherwise react to mouse hovers */
        onClick={isMobile ? onMouseOver : noop}
        onFocus={!isMobile ? onMouseOver : noop}
        onMouseOver={!isMobile ? onMouseOver : noop}
        onMouseMove={!isMobile ? onMouseOver : noop}
        onMouseOut={onMouseOut}
        onBlur={onMouseOut}
      />

      {/* Row label */}
      <text
        className="name"
        style={{ pointerEvents: 'none', textAnchor: 'end' }}
        transform={`translate(${LABEL_MAX_WIDTH - 1.5 * PADDING_Y}, ${TEXT_ADJUST_Y})`}
      >
        {label}
      </text>

      {/* Row content */}
      {children}
    </g>
  );
};

const HorizontalBar = ({
  className,
  fill,
  range,
  scale,
}) => {
  // Don't render if the range is not valid
  if (!isArray(range) || !isFinite(range[0]) || !isFinite(range[1])) return null;

  const x1 = Math.min(range[0], range[1]);
  const x2 = Math.max(range[0], range[1]);
  const width = scale(x2) - scale(x1);

  // Don't render if the width is not positive
  if (width <= 0) return null;

  return (
    <rect
      className={className}
      fill={fill}
      height={ROW_HEIGHT}
      opacity={RECT_OPACITY}
      shapeRendering="crispEdges"
      style={{ pointerEvents: 'none' }}
      x={LABEL_MAX_WIDTH + scale(x1)}
      width={width}
    />
  );
};

const QuestionMarkIfNoData = ({ datapoint, scale }) => {
  // If the mode is unknown, don't need to show the question mark
  if (datapoint.mode === 'unknown') return null;

  // If both the value and capacity fills are there, don't show the question mark 
  const value = datapoint.isStorage ? datapoint.storage : datapoint.production;
  if (datapoint.capacity !== undefined && value !== undefined) return null;

  return (
    <text
      className="unknown"
      transform={`translate(1, ${TEXT_ADJUST_Y})`}
      style={{ pointerEvents: 'none', fill: 'darkgray' }}
      x={LABEL_MAX_WIDTH + scale(0)}
    >
      ?
    </text>
  );
};

const CountryCarbonEmissionsTable = React.memo(({
  data,
  electricityMixMode,
  exchangeData,
  height,
  isMobile,
  productionData,
  onProductionRowMouseOver,
  onProductionRowMouseOut,
  onExchangeRowMouseOver,
  onExchangeRowMouseOut,
  width,
}) => {
  const { productionY, exchangeFlagX, exchangeY } = getDataBlockPositions(productionData, exchangeData);

  const maxCO2eqExport = d3Max(exchangeData, d => Math.max(0, -d.tCo2eqPerMin));
  const maxCO2eqImport = d3Max(exchangeData, d => Math.max(0, d.tCo2eqPerMin));
  const maxCO2eqProduction = d3Max(productionData, d => d.tCo2eqPerMin);

  // in tCO₂eq/min
  const co2Scale = scaleLinear()
    .domain([
      -maxCO2eqExport || 0,
      Math.max(
        maxCO2eqProduction || 0,
        maxCO2eqImport || 0
      ),
    ])
    .range([0, width - LABEL_MAX_WIDTH - PADDING_X]);

  const formatTick = (t) => {
    const [x1, x2] = co2Scale.domain();
    if (x2 - x1 <= 1) return `${t * 1e3} kg/min`;
    return `${t} t/min`;
  };

  return (
    <svg className="country-table" height={height} style={{ overflow: 'visible' }}>
      <Axis
        formatTick={formatTick}
        height={height}
        scale={co2Scale}
      />
      <g transform={`translate(0, ${productionY})`}>
        {productionData.map((d, index) => (
          <Row
            key={d.mode}
            index={index}
            label={__(d.mode)}
            width={width}
            onMouseOver={ev => onProductionRowMouseOver(d.mode, data, ev)}
            onMouseOut={onProductionRowMouseOut}
            isMobile={isMobile}
          >
            <HorizontalBar
              className="production"
              fill={modeColor[d.mode]}
              range={[0, Math.abs(d.tCo2eqPerMin)]}
              scale={co2Scale}
            />
            <QuestionMarkIfNoData
              datapoint={d}
              scale={co2Scale}
            />
          </Row>
        ))}
      </g>
      <g transform={`translate(0, ${exchangeY})`}>
        {exchangeData.map((d, index) => (
          <Row
            key={d.mode}
            index={index}
            label={d.mode}
            width={width}
            onMouseOver={ev => onExchangeRowMouseOver(d.mode, data, ev)}
            onMouseOut={onExchangeRowMouseOut}
            isMobile={isMobile}
          >
            <image
              style={{ pointerEvents: 'none' }}
              x={exchangeFlagX}
              xlinkHref={flagUri(d.mode)}
            />
            <HorizontalBar
              className="exchange"
              fill="gray"
              range={[0, d.tCo2eqPerMin]}
              scale={co2Scale}
            />
          </Row>
        ))}
      </g>
    </svg>
  );
});

const CountryElectricityProductionTable = React.memo(({
  data,
  electricityMixMode,
  exchangeData,
  height,
  isMobile,
  productionData,
  onProductionRowMouseOver,
  onProductionRowMouseOut,
  onExchangeRowMouseOver,
  onExchangeRowMouseOut,
  width,
}) => {
  const co2ColorScale = useCo2ColorScale();

  const { productionY, exchangeFlagX, exchangeY } = getDataBlockPositions(productionData, exchangeData);

  // Power in MW
  const powerScale = scaleLinear()
    .domain([
      Math.min(
        -data.maxStorageCapacity || 0,
        -data.maxStorage || 0,
        -data.maxExport || 0,
        -data.maxExportCapacity || 0
      ),
      Math.max(
        data.maxCapacity || 0,
        data.maxProduction || 0,
        data.maxDischarge || 0,
        data.maxStorageCapacity || 0,
        data.maxImport || 0,
        data.maxImportCapacity || 0
      ),
    ])
    .range([0, width - LABEL_MAX_WIDTH - PADDING_X]);

  const formatTick = (t) => {
    const [x1, x2] = powerScale.domain();
    if (x2 - x1 <= 1) return `${t * 1e3} kW`;
    if (x2 - x1 <= 1e3) return `${t} MW`;
    return `${t * 1e-3} GW`;
  };

  return (
    <svg className="country-table" height={height} style={{ overflow: 'visible' }}>
      <Axis
        formatTick={formatTick}
        height={height}
        scale={powerScale}
      />
      <g transform={`translate(0, ${productionY})`}>
        {productionData.map((d, index) => (
          <Row
            key={d.mode}
            index={index}
            label={__(d.mode)}
            width={width}
            onMouseOver={ev => onProductionRowMouseOver(d.mode, data, ev)}
            onMouseOut={onProductionRowMouseOut}
            isMobile={isMobile}
          >
            <HorizontalBar
              className="capacity"
              fill="rgba(0, 0, 0, 0.15)"
              range={d.isStorage ? [-d.capacity, d.capacity] : [0, d.capacity]}
              scale={powerScale}
            />
            <HorizontalBar
              className="production"
              fill={modeColor[d.mode]}
              range={d.isStorage ? [0, -d.storage] : [0, d.production]}
              scale={powerScale}
            />
            <QuestionMarkIfNoData
              datapoint={d}
              scale={powerScale}
            />
          </Row>
        ))}
      </g>
      <g transform={`translate(0, ${exchangeY})`}>
        {exchangeData.map((d, index) => (
          <Row
            key={d.mode}
            index={index}
            label={d.mode}
            width={width}
            onMouseOver={ev => onExchangeRowMouseOver(d.mode, data, ev)}
            onMouseOut={onExchangeRowMouseOut}
            isMobile={isMobile}
          >
            <image
              style={{ pointerEvents: 'none' }}
              x={exchangeFlagX}
              xlinkHref={flagUri(d.mode)}
            />
            <HorizontalBar
              className="capacity"
              fill="rgba(0, 0, 0, 0.15)"
              range={d.exchangeCapacityRange}
              scale={powerScale}
            />
            <HorizontalBar
              className="exchange"
              fill={co2ColorScale(d.gCo2eqPerkWh)}
              range={[0, d.exchange]}
              scale={powerScale}
            />
          </Row>
        ))}
      </g>
    </svg>
  );
});

const mapStateToProps = state => ({
  displayByEmissions: state.application.tableDisplayEmissions,
  electricityMixMode: state.application.electricityMixMode,
  isMobile: state.application.isMobile,
});

const CountryTable = ({
  displayByEmissions,
  electricityMixMode,
  isMobile,
}) => {
  const ref = useRef(null);
  const width = useWidthObserver(ref);

  const exchangeKeys = useCurrentZoneExchangeKeys();
  const data = useCurrentZoneData();

  const productionData = useMemo(
    () => getProductionData(data),
    [data]
  );
  const exchangeData = useMemo(
    () => getExchangeData(data, exchangeKeys, electricityMixMode),
    [data, exchangeKeys, electricityMixMode]
  );

  const [productionTooltip, setProductionTooltip] = useState(null);
  const [exchangeTooltip, setExchangeTooltip] = useState(null);

  const handleProductionRowMouseOver = (mode, zoneData, ev) => {
    dispatchApplication('co2ColorbarValue', getProductionCo2Intensity(mode, zoneData));
    setProductionTooltip({ mode, zoneData, position: getTooltipPosition(isMobile, { x: ev.clientX, y: ev.clientY }) });
  };

  const handleProductionRowMouseOut = () => {
    dispatchApplication('co2ColorbarValue', null);
    setProductionTooltip(null);
  };

  const handleExchangeRowMouseOver = (mode, zoneData, ev) => {
    dispatchApplication('co2ColorbarValue', getExchangeCo2Intensity(mode, zoneData, electricityMixMode));
    setExchangeTooltip({ mode, zoneData, position: getTooltipPosition(isMobile, { x: ev.clientX, y: ev.clientY }) });
  };

  const handleExchangeRowMouseOut = () => {
    dispatchApplication('co2ColorbarValue', null);
    setExchangeTooltip(null);
  };

  const { exchangeY, exchangeHeight } = getDataBlockPositions(productionData, exchangeData);
  const height = exchangeY + exchangeHeight;

  return (
    <div className="country-table-container" ref={ref}>
      {displayByEmissions ? (
        <CountryCarbonEmissionsTable
          electricityMixMode={electricityMixMode}
          data={data}
          productionData={productionData}
          exchangeData={exchangeData}
          onProductionRowMouseOver={handleProductionRowMouseOver}
          onProductionRowMouseOut={handleProductionRowMouseOut}
          onExchangeRowMouseOver={handleExchangeRowMouseOver}
          onExchangeRowMouseOut={handleExchangeRowMouseOut}
          width={width}
          height={height}
          isMobile={isMobile}
        />
      ) : (
        <CountryElectricityProductionTable
          electricityMixMode={electricityMixMode}
          data={data}
          productionData={productionData}
          exchangeData={exchangeData}
          onProductionRowMouseOver={handleProductionRowMouseOver}
          onProductionRowMouseOut={handleProductionRowMouseOut}
          onExchangeRowMouseOver={handleExchangeRowMouseOver}
          onExchangeRowMouseOut={handleExchangeRowMouseOut}
          width={width}
          height={height}
          isMobile={isMobile}
        />
      )}
      {productionTooltip && (
        <CountryPanelProductionTooltip
          mode={productionTooltip.mode}
          position={productionTooltip.position}
          zoneData={productionTooltip.zoneData}
        />
      )}
      {exchangeTooltip && (
        <CountryPanelExchangeTooltip
          exchangeKey={exchangeTooltip.mode}
          position={exchangeTooltip.position}
          zoneData={exchangeTooltip.zoneData}
        />
      )}
      <CountryTableOverlayIfNoData />
    </div>
  );
};

export default connect(mapStateToProps)(CountryTable);
