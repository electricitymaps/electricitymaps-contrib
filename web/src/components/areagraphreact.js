import React from 'react';
import moment from 'moment';
import { connect } from 'react-redux';

import formatting from '../helpers/formatting';
import { modeOrder, modeColor } from '../helpers/constants';

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

const TimeAxis = ({ domain, range, height }) => {
  const scale = d3.scaleTime();
  scale.domain(domain);
  scale.range(range);

  const tickSizeOuter = 6;
  const strokeWidth = 1;
  const halfWidth = strokeWidth / 2;
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
  domain,
  range,
  label,
  width,
}) => {
  const scale = d3.scaleLinear();
  scale.domain(domain);
  scale.range(range);

  const tickSizeOuter = 6;
  const strokeWidth = 1;
  const halfWidth = strokeWidth / 2;
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

const mapStateToProps = (state, props) => ({
  currentMoment: moment(state.application.customDate || (state.data.grid || {}).datetime),
  data: props.dataSelector(state),
  displayByEmissions: state.application.tableDisplayEmissions,
  electricityMixMode: state.application.electricityMixMode,
});

const AreaGraph = ({
  currentMoment,
  data,
  displayByEmissions,
  electricityMixMode,
  id,
}) => {
  if (!data) return null;

  // Create scales
  const z = d3.scaleOrdinal();

  let maxTotalValue = getMaxTotalValue(data, displayByEmissions);

  const format = formatting.scalePower(maxTotalValue);
  const formattingFactor = !displayByEmissions ? format.formattingFactor : 1;
  maxTotalValue /= formattingFactor;

  const firstDatetime = data[0] && moment(data[0].stateDatetime).toDate();
  const lastDatetime = currentMoment.toDate();

  const { exchangeKeysSet, graphData } = prepareGraphData(data, displayByEmissions, electricityMixMode, formattingFactor);

  // TODO: update these dynamically
  const width = 330;
  const height = 160;

  // Prepare stack
  // Order is defined here, from bottom to top
  let stackKeys = modeOrder;
  if (electricityMixMode === 'consumption') {
    stackKeys = stackKeys.concat(exchangeKeysSet.values());
  }
  const stack = d3.stack()
    .offset(d3.stackOffsetDiverging)
    .keys(stackKeys)(graphData);

  // Cache datetimes
  const datetimes = graphData.map(d => d.datetime);

  const valuesLabel = !displayByEmissions ? format.unit : 'tCO2eq/min';
  const valuesScaleRange = [height - X_AXIS_HEIGHT, Y_AXIS_PADDING];
  const valuesScaleDomain = [0, maxTotalValue * 1.1];

  const timeScaleRange = [0, width - Y_AXIS_WIDTH];
  const timeScaleDomain = firstDatetime && lastDatetime
    ? [firstDatetime, lastDatetime]
    : d3.extent(graphData, d => d.datetime);

  return (
    <svg id={id}>
      <TimeAxis
        domain={timeScaleDomain}
        range={timeScaleRange}
        height={height}
      />
      <ValuesAxis
        domain={valuesScaleDomain}
        range={valuesScaleRange}
        label={valuesLabel}
        width={width}
      />
    </svg>
  );
};

export default connect(mapStateToProps)(AreaGraph);
