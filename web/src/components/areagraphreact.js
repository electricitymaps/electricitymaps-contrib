import React, { useState, useEffect } from 'react';
import moment from 'moment';
import { connect } from 'react-redux';

import formatting from '../helpers/formatting';
import { modeOrder, modeColor } from '../helpers/constants';
import { getCo2Scale } from '../helpers/scales';

const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-axis'),
  require('d3-collection'),
  require('d3-scale'),
  require('d3-shape'),
);

const X_AXIS_HEIGHT = 20;
const Y_AXIS_WIDTH = 35;
const Y_AXIS_PADDING = 4;

const getMaxTotalValue = (data, displayByEmissions) =>
  d3.max(data, d => (
    displayByEmissions
      ? (d.totalCo2Production + d.totalCo2Import + d.totalCo2Discharge) / 1e6 / 60.0 // in tCO2eq/min
      : (d.totalProduction + d.totalImport + d.totalDischarge) // in MW
  ));

const TimeAxis = ({ scale, height }) => {
  const tickSizeOuter = 6;
  const strokeWidth = 1;
  const halfWidth = strokeWidth / 2;
  const range = scale.range();
  const range0 = range[0] + halfWidth;
  const range1 = range[range.length - 1] + halfWidth;
  const values = scale.ticks(5);

  const formatTick = d => moment(d).format('LT');

  return (
    <g
      className="x axis"
      transform={`translate(-1 ${height - X_AXIS_HEIGHT - 1})`}
      fill="none"
      fontSize="10"
      fontFamily="sans-serif"
      textAnchor="middle"
      style={{ pointerEvents: 'none' }}
    >
      <path className="domain" stroke="currentColor" d={`M${range0},${tickSizeOuter}V${halfWidth}H${range1}V${tickSizeOuter}`} />
      {values.map(v => (
        <g key={`tick-${v}`} className="tick" opacity={1} transform={`translate(${scale(v)},0)`}>
          <line stroke="currentColor" y2="6" />
          <text fill="currentColor" y="9" dy="0.71em">{formatTick(v)}</text>
        </g>
      ))}
    </g>
  );
};

const ValuesAxis = ({
  scale,
  label,
  width,
}) => {
  const tickSizeOuter = 6;
  const strokeWidth = 1;
  const halfWidth = strokeWidth / 2;
  const range = scale.range();
  const range0 = range[0] + halfWidth;
  const range1 = range[range.length - 1] + halfWidth;
  const values = scale.ticks(5);

  return (
    <g
      className="y axis"
      transform={`translate(${width - Y_AXIS_WIDTH - 1} -1)`}
      fill="none"
      fontSize="10"
      fontFamily="sans-serif"
      textAnchor="start"
      style={{ pointerEvents: 'none' }}
    >
      <text className="label" transform="translate(35, 80) rotate(-90)">{label}</text>
      <path className="domain" stroke="currentColor" d={`M${tickSizeOuter},${range0}H${halfWidth}V${range1}H${tickSizeOuter}`} />
      {values.map(v => (
        <g key={`tick-${v}`} className="tick" opacity={1} transform={`translate(0,${scale(v)})`}>
          <line stroke="currentColor" x2="6" />
          <text fill="currentColor" x="9" y="3" dx="0.32em">{v}</text>
        </g>
      ))}
    </g>
  );
};

// TODO: Refactor this function to make it more readable
const prepareGraphData = (data, displayByEmissions, electricityMixMode, formattingFactor) => {
  const exchangeKeysSet = d3.set();
  const graphData = data.map((d) => {
    const obj = {
      datetime: moment(d.stateDatetime).toDate(),
    };
    // Add production
    modeOrder.forEach((k) => {
      const isStorage = k.indexOf('storage') !== -1;
      const value = isStorage
        ? -1 * Math.min(0, (d.storage || {})[k.replace(' storage', '')])
        : (d.production || {})[k];
      // in GW or MW
      obj[k] = value / formattingFactor;
      if (Number.isFinite(value) && displayByEmissions && obj[k] != null) {
        // in tCO2eq/min
        if (isStorage && obj[k] >= 0) {
          obj[k] *= d.dischargeCo2Intensities[k.replace(' storage', '')] / 1e3 / 60.0;
        } else {
          obj[k] *= d.productionCo2Intensities[k] / 1e3 / 60.0;
        }
      }
    });
    if (electricityMixMode === 'consumption') {
      // Add exchange
      d3.entries(d.exchange).forEach((o) => {
        exchangeKeysSet.add(o.key);
        // in GW or MW
        obj[o.key] = Math.max(0, o.value / formattingFactor);
        if (Number.isFinite(o.value) && displayByEmissions && obj[o.key] != null) {
          // in tCO2eq/min
          obj[o.key] *= d.exchangeCo2Intensities[o.key] / 1e3 / 60.0;
        }
      });
    }
    // Keep a pointer to original data
    obj._countryData = d;
    return obj;
  });
  return { exchangeKeysSet, graphData };
};

// Regular production mode or exchange fill as a fallback
const fillColor = (key, displayByEmissions) =>
  modeColor[key] || (displayByEmissions ? 'darkgray' : `url(#areagraph-exchange-${key})`);

const detectPosition = (ev, datetimes, timeScale, svgRef) => {
  if (!datetimes.length) return null;
  const dx = ev.pageX
    ? (ev.pageX - svgRef.current.getBoundingClientRect().left)
    : (d3.touches(this)[0][0]);
  const datetime = timeScale.invert(dx);
  // Find data point closest to
  let i = d3.bisectLeft(datetimes, datetime);
  if (i > 0 && datetime - datetimes[i - 1] < datetimes[i] - datetime) i -= 1;
  if (i > datetimes.length - 1) i = datetimes.length - 1;
  return i;
};

const mapStateToProps = (state, props) => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  currentMoment: moment(state.application.customDate || (state.data.grid || {}).datetime),
  data: props.dataSelector(state),
  displayByEmissions: state.application.tableDisplayEmissions,
  electricityMixMode: state.application.electricityMixMode,
  selectedIndex: state.application.selectedZoneTimeIndex,
});

const AreaGraph = ({
  colorBlindModeEnabled,
  currentMoment,
  data,
  displayByEmissions,
  electricityMixMode,
  id,
  selectedIndex,
  // TODO
  layerMouseMoveHandler,
  layerMouseOutHandler,
  mouseMoveHandler,
  mouseOutHandler,
}) => {
  const svgRef = React.createRef();
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(3);
  const [container, setContainer] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const updateDimensions = () => {
      if (svgRef && svgRef.current) {
        const { width, height } = svgRef.current.getBoundingClientRect();
        setContainer({ width, height });
      }
    };
    // Initialize dimensions if they are not set yet
    if (!container.width || !container.height) {
      updateDimensions();
    }
    // Update container dimensions on every resize
    window.addEventListener('resize', updateDimensions);
    return () => {
      window.removeEventListener('resize', updateDimensions);
    };
  });

  if (!data) return null;

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);

  let maxTotalValue = getMaxTotalValue(data, displayByEmissions);

  const format = formatting.scalePower(maxTotalValue);
  const formattingFactor = !displayByEmissions ? format.formattingFactor : 1;
  maxTotalValue /= formattingFactor;

  const firstDatetime = data[0] && moment(data[0].stateDatetime).toDate();
  const lastDatetime = currentMoment.toDate();

  const { exchangeKeysSet, graphData } = prepareGraphData(data, displayByEmissions, electricityMixMode, formattingFactor);

  // Prepare stack
  // Order is defined here, from bottom to top
  let stackKeys = modeOrder;
  if (electricityMixMode === 'consumption') {
    stackKeys = stackKeys.concat(exchangeKeysSet.values());
  }
  const stackedData = d3.stack()
    .offset(d3.stackOffsetDiverging)
    .keys(stackKeys)(graphData);

  // Cache datetimes
  const datetimes = graphData.map(d => d.datetime);

  const timeScale = d3.scaleTime();
  timeScale.domain(firstDatetime && lastDatetime
    ? [firstDatetime, lastDatetime]
    : d3.extent(graphData, d => d.datetime));
  timeScale.range([0, container.width - Y_AXIS_WIDTH]);

  const valuesLabel = !displayByEmissions ? format.unit : 'tCO2eq/min';
  const valuesScale = d3.scaleLinear();
  valuesScale.domain([0, maxTotalValue * 1.1]);
  valuesScale.range([container.height - X_AXIS_HEIGHT, Y_AXIS_PADDING]);

  const area = d3.area()
    .x(d => timeScale(d.data.datetime))
    .y0(d => valuesScale(d[0]))
    .y1(d => valuesScale(d[1]))
    .defined(d => Number.isFinite(d[1]));

  let mouseOutTimeout;
  const handleLayerMouseMove = (ev, layer, ind) => {
    if (mouseOutTimeout) {
      clearTimeout(mouseOutTimeout);
      mouseOutTimeout = undefined;
    }
    setSelectedLayerIndex(ind);
    const i = detectPosition(ev, datetimes, timeScale, svgRef);
    if (layerMouseMoveHandler) {
      const position = { x: ev.clientX - 7, y: svgRef.current.getBoundingClientRect().top - 7 };
      layerMouseMoveHandler(stackKeys[ind], position, layer[i].data._countryData);
    }
    if (mouseMoveHandler) {
      mouseMoveHandler(layer[i].data._countryData, i);
    }
  };

  const handleLayerMouseOut = () => {
    mouseOutTimeout = setTimeout(() => {
      setSelectedLayerIndex(undefined);
      if (mouseOutHandler) {
        mouseOutHandler();
      }
      if (layerMouseOutHandler) {
        layerMouseOutHandler();
      }
    }, 50);
  };

  return (
    <svg id={id} ref={svgRef}>
      <TimeAxis
        scale={timeScale}
        height={container.height}
      />
      <ValuesAxis
        label={valuesLabel}
        scale={valuesScale}
        width={container.width}
      />
      <g>
        {stackedData.map((layer, ind) => (
          <path
            key={stackKeys[ind]}
            className={`area layer ${stackKeys[ind]}`}
            fill={fillColor(stackKeys[ind], displayByEmissions)}
            d={area(layer)}
            onFocus={ev => handleLayerMouseMove(ev, layer, ind)}
            onMouseOver={ev => handleLayerMouseMove(ev, layer, ind)}
            onMouseMove={ev => handleLayerMouseMove(ev, layer, ind)}
            onMouseOut={handleLayerMouseOut}
            onBlur={handleLayerMouseOut}
          />
        ))}
      </g>
      {selectedIndex !== null && selectedIndex !== undefined && (
        <line
          className="vertical-line"
          style={{
            display: 'block',
            pointerEvents: 'none',
            shapeRendering: 'crispEdges',
          }}
          x1={timeScale(graphData[selectedIndex].datetime)}
          x2={timeScale(graphData[selectedIndex].datetime)}
          y1={valuesScale.range()[0]}
          y2={valuesScale.range()[1]}
        />
      )}
      {selectedIndex !== null && selectedIndex !== undefined && stackedData[selectedLayerIndex] && (
        <circle
          r="6"
          style={{
            display: 'block',
            pointerEvents: 'none',
            shapeRendering: 'crispEdges',
            stroke: 'black',
            strokeWidth: 1.5,
            fill: fillColor(stackKeys[selectedLayerIndex], displayByEmissions),
          }}
          cx={timeScale(graphData[selectedIndex].datetime)}
          cy={valuesScale(stackedData[selectedLayerIndex][selectedIndex][1])}
        />
      )}
      <React.Fragment>
        {exchangeKeysSet.values().map(key => (
          <linearGradient
            key={key}
            gradientUnits="userSpaceOnUse"
            id={`areagraph-exchange-${key}`}
            x1={timeScale.range()[0]}
            x2={timeScale.range()[1]}
          >
            {graphData.map(d => (
              <stop
                key={d.datetime}
                offset={`${(timeScale(d.datetime) - timeScale.range()[0]) / (timeScale.range()[1] - timeScale.range()[0]) * 100.0}%`}
                stopColor={d._countryData.exchangeCo2Intensities ? co2ColorScale(d._countryData.exchangeCo2Intensities[key]) : 'darkgray'}
              />
            ))}
          </linearGradient>
        ))}
      </React.Fragment>
    </svg>
  );
};

export default connect(mapStateToProps)(AreaGraph);
