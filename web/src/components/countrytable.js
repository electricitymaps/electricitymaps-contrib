import React, { useRef, useEffect, useState } from 'react';
import { connect } from 'react-redux';
import { scaleLinear } from 'd3-scale';
import { max as d3Max, min as d3Min } from 'd3-array';
import { precisionPrefix, formatPrefix } from 'd3-format';
import { isArray, isFinite } from 'lodash';

import { dispatchApplication } from '../store';
import { getCo2Scale } from '../helpers/scales';
import { modeOrder, modeColor } from '../helpers/constants';
import { getSelectedZoneExchangeKeys } from '../helpers/history';
import { getCurrentZoneData } from '../helpers/redux';
import { flagUri } from '../helpers/flags';
import { __ } from '../helpers/translation';

import NoDataOverlay from './nodataoverlay';

const LABEL_MAX_WIDTH = 102;
const TEXT_ADJUST_Y = 11;
const ROW_HEIGHT = 13;
const PADDING_Y = 7;
const PADDING_X = 5;
const FLAG_SIZE = 16;
const RECT_OPACITY = 0.8;
const X_AXIS_HEIGHT = 15;
const SCALE_TICKS = 4;

function handleRowMouseMove(isMobile, mode, data, ev) {
  // If in mobile mode, put the tooltip to the top of the screen for
  // readability, otherwise float it depending on the cursor position.
  const tooltipPosition = !isMobile
    ? { x: ev.clientX - 7, y: ev.clientY - 7 }
    : { x: 0, y: 0 };
  dispatchApplication('tooltipPosition', tooltipPosition);
  dispatchApplication('tooltipZoneData', data);
  dispatchApplication('tooltipDisplayMode', mode);
}

function handleRowMouseOut() {
  dispatchApplication('tooltipDisplayMode', null);
}

const rangeZeroTo = value => (value < 0 ? [value, 0] : [0, value]);

const getProductionData = data => modeOrder.map((mode) => {
  const isStorage = mode.indexOf('storage') !== -1;
  const key = mode.replace(' storage', '');

  // Power in MW
  const capacity = (data.capacity || {})[key];
  const production = (data.production || {})[key];
  const storage = (data.storage || {})[key];

  // Production CO2 intensity
  const gCo2eqPerkWh = ((
    isStorage ? (
      storage > 0
        ? data.storageCo2Intensities
        : data.dischargeCo2Intensities
    ) : (
      data.productionCo2Intensities
    )
  ) || {})[key];

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
  const key = mode;

  // Power in MW
  const exchange = (data.exchange || {})[key];
  const exchangeCapacityRange = (data.exchangeCapacities || {})[key];

  // Exchange CO2 intensity
  const gCo2eqPerkWh =
    exchange > 0 ? (
      (data.exchangeCo2Intensities || {})[key]
    ) : (
      electricityMixMode === 'consumption'
        ? data.co2intensity
        : data.co2intensityProduction
    );

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

const RowBackground = ({ width, height, isMobile, data, mode }) => (
  <rect
    y="-1"
    fill="transparent"
    width={width}
    height={height}
    onFocus={ev => handleRowMouseMove(isMobile, mode, data, ev)}
    onMouseOver={ev => handleRowMouseMove(isMobile, mode, data, ev)}
    onMouseMove={ev => handleRowMouseMove(isMobile, mode, data, ev)}
    onMouseOut={handleRowMouseOut}
    onBlur={handleRowMouseOut}
  />
);

const RowLabel = ({ label }) => (
  <text
    className="name"
    style={{ pointerEvents: 'none', textAnchor: 'end' }}
    transform={`translate(${LABEL_MAX_WIDTH - 1.5 * PADDING_Y}, ${TEXT_ADJUST_Y})`}
  >
    {label}
  </text>
);

const HorizontalBar = ({ className, fill, range, scale }) => {
  // Don't render if the range is not valid
  if (!isArray(range) || !isFinite(range[0]) || !isFinite(range[1])) return null;

  return (
    <rect
      className={className}
      height={ROW_HEIGHT}
      height={ROW_HEIGHT}
      opacity={RECT_OPACITY}
      shapeRendering="crispEdges"
      style={{ pointerEvents: 'none' }}
      fill={fill}
      x={LABEL_MAX_WIDTH + scale(range[0])}
      width={scale(range[1]) - scale(range[0])}
    />
  );
};

const UnknownValue = ({ datapoint, scale }) => {
  // const visible = displayByEmissions && getExchangeCo2eq(datapoint) === undefined;
  const visible = (datapoint.capacity === undefined || datapoint.capacity > 0)
    && datapoint.mode !== 'unknown'
    && (datapoint.isStorage ? datapoint.storage === undefined : datapoint.production === undefined);

  if (!visible) return null;

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
}

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  displayByEmissions: state.application.tableDisplayEmissions,
  data: getCurrentZoneData(state),
  electricityMixMode: state.application.electricityMixMode,
  exchangeKeys: getSelectedZoneExchangeKeys(state),
  isMobile: state.application.isMobile,
});

const CountryTable = ({
  colorBlindModeEnabled,
  data,
  displayByEmissions,
  electricityMixMode,
  exchangeKeys,
  isMobile,
}) => {
  const ref = useRef(null);
  const [containerWidth, setContainerWidth] = useState(0);

  // Container resize hook
  useEffect(() => {
    const updateContainerWidth = () => {
      if (ref.current) {
        setContainerWidth(ref.current.getBoundingClientRect().width);
      }
    };
    // Initialize width if it's not set yet
    if (!containerWidth) {
      updateContainerWidth();
    }
    // Update container width on every resize
    window.addEventListener('resize', updateContainerWidth);
    return () => {
      window.removeEventListener('resize', updateContainerWidth);
    };
  });

  // const isMissingParser = !data.hasParser;

  const productionData = getProductionData(data);
  const exchangeData = getExchangeData(data, exchangeKeys, electricityMixMode);

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const exchangeLabelLength = d3Max(exchangeData, ed => ed.mode.length) * 8;
  const barMaxWidth = containerWidth - LABEL_MAX_WIDTH - PADDING_X;

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
    .range([0, barMaxWidth]);
  const formatPowerScaleTick = (t) => {
    const scaleSpan = powerScale.domain()[1] - powerScale.domain()[0];
    if (scaleSpan <= 1) return `${t * 1e3} kW`;
    if (scaleSpan <= 1e3) return `${t} MW`;
    return `${t * 1e-3} GW`;
  };

  const maxCO2eqExport = d3Max(exchangeData, d => Math.max(0, -d.tCo2eqPerMin));
  const maxCO2eqImport = d3Max(exchangeData, d => Math.max(0, d.tCo2eqPerMin));
  const maxCO2eqProduction = d3Max(productionData, d => d.tCo2eqPerMin);

  // in tCO2eq/min
  const co2Scale = scaleLinear()
    .domain([
      -maxCO2eqExport || 0,
      Math.max(
        maxCO2eqProduction || 0,
        maxCO2eqImport || 0
      ),
    ])
    .range([0, barMaxWidth]);
  const formatCo2ScaleTick = (t) => {
    const scaleSpan = co2Scale.domain()[1] - co2Scale.domain()[0];
    if (scaleSpan <= 1) return `${t * 1e3} kg / min`;
    return `${t} t / min`;
  };
  
  const valueScale = displayByEmissions ? co2Scale : powerScale;

  const ticks = valueScale.ticks(SCALE_TICKS);

  const productionHeight = productionData.length * (ROW_HEIGHT + PADDING_Y);
  const exchangesHeight = exchangeData.length * (ROW_HEIGHT + PADDING_Y);

  const productionY = X_AXIS_HEIGHT + PADDING_Y;
  const exchangesY = productionY + productionHeight + ROW_HEIGHT + PADDING_Y;
  
  const containerHeight = exchangesY + exchangesHeight;

  return (
    <div className="country-table-container">
      <svg className="country-table" height={containerHeight} style={{ overflow: 'visible' }} ref={ref}>
        {displayByEmissions ? (
          <Axis
            formatTick={formatCo2ScaleTick}
            height={containerWidth}
            scale={co2Scale}
          />
        ) : (
          <Axis
            formatTick={formatPowerScaleTick}
            height={containerWidth}
            scale={powerScale}
          />
        )}
        <g transform={`translate(0, ${productionY})`}>
          {productionData.map((d, ind) => (
            <g key={d.mode} className="row" transform={`translate(0, ${ind * (ROW_HEIGHT + PADDING_Y)})`}>
              <RowBackground
                width={containerWidth}
                height={ROW_HEIGHT + PADDING_Y}
                isMobile={isMobile}
                mode={d.mode}
                data={data}
              />

              <RowLabel label={__(d.mode)} />

              {displayByEmissions ? (
                <HorizontalBar
                  className="production"
                  fill={modeColor[d.mode]}
                  range={rangeZeroTo(d.tCo2eqPerMin)}
                  scale={co2Scale}
                />
              ) : (
                <React.Fragment>
                  <HorizontalBar
                    className="capacity"
                    fill="rgba(0, 0, 0, 0.15)"
                    range={d.isStorage ? [-d.capacity, d.capacity] : rangeZeroTo(d.capacity)}
                    scale={powerScale}
                  />
                  <HorizontalBar
                    className="production"
                    fill={modeColor[d.mode]}
                    range={d.isStorage ? [-d.storage, d.production] : rangeZeroTo(d.production)}
                    scale={powerScale}
                  />
                </React.Fragment>
              )}

              <UnknownValue
                datapoint={d}
                scale={valueScale}
              />
            </g>
          ))}
        </g>
        <g transform={`translate(0, ${exchangesY})`}>
          {exchangeData.map((d, ind) => {
            return (
              <g key={d.mode} className="row" transform={`translate(0, ${ind * (ROW_HEIGHT + PADDING_Y)})`}>
                <RowBackground
                  width={containerWidth}
                  height={ROW_HEIGHT + PADDING_Y}
                  isMobile={isMobile}
                  mode={d.mode}
                  data={data}
                />

                <image
                  width={FLAG_SIZE}
                  height={FLAG_SIZE}
                  style={{ pointerEvents: 'none' }}
                  x={LABEL_MAX_WIDTH - 4.0 * PADDING_X - FLAG_SIZE - exchangeLabelLength}
                  xlinkHref={flagUri(d.mode, FLAG_SIZE)}
                />
                <RowLabel label={d.mode} />

                {displayByEmissions ? (
                  <HorizontalBar
                    className="exchange"
                    fill="gray"
                    range={rangeZeroTo(d.tCo2eqPerMin)}
                    scale={co2Scale}
                  />
                ) : (
                  <React.Fragment>
                    <HorizontalBar
                      className="capacity"
                      fill="rgba(0, 0, 0, 0.15)"
                      range={d.exchangeCapacityRange}
                      scale={powerScale}
                    />
                    <HorizontalBar
                      className="exchange"
                      fill={d.gCo2eqPerkWh ? co2ColorScale(d.gCo2eqPerkWh) : 'gray'}
                      range={rangeZeroTo(d.exchange)}
                      scale={powerScale}
                    />
                  </React.Fragment>
                )}
              </g>
            );
          })}
        </g>
      </svg>
      <NoDataOverlay />
    </div>
  );
};

export default connect(mapStateToProps)(CountryTable);
