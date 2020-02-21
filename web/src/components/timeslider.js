import React, { useRef, useState, useEffect } from 'react';
import { connect, useDispatch } from 'react-redux';
import { first, last } from 'lodash';
import moment from 'moment';

import { __ } from '../helpers/translation';

const d3 = Object.assign(
  {},
  require('d3-scale'),
);

const NUMBER_OF_TICKS = 5;
const AXIS_MARGIN_LEFT = 5;

const sampledTickValues = (data) => {
  const tickValues = [];
  if (data.length >= NUMBER_OF_TICKS) {
    for (let i = 0; i < NUMBER_OF_TICKS; i += 1) {
      const sampleIndex = Math.floor(((data.length - 1) / (NUMBER_OF_TICKS - 1)) * (i));
      tickValues.push(data[sampleIndex]);
    }
  }
  return tickValues;
};

const renderTick = (v, ind) =>
  (ind === NUMBER_OF_TICKS - 1 ? __('country-panel.now') : moment(v).format('LT')); // Localized time, e.g. "8:30 PM"

const getSelectedZoneHistory = state =>
  state.data.histories[state.application.selectedZoneName] || [];

const mapStateToProps = state => ({
  selectedIndex: state.application.selectedZoneTimeIndex,
  timestamps: getSelectedZoneHistory(state).map(d => moment(d.stateDatetime).toDate()),
});

const TimeSlider = ({ className, timestamps, selectedIndex }) => {
  const ref = useRef(null);
  const dispatch = useDispatch();
  const [width, setWidth] = useState(0);
  const [anchoredIndex, setAnchoredIndex] = useState(null);

  // Container resize hook
  useEffect(() => {
    const updateWidth = () => {
      if (ref.current) {
        setWidth(ref.current.getBoundingClientRect().width - AXIS_MARGIN_LEFT);
      }
    };
    // Initialize width if it's not set yet
    if (!width) {
      updateWidth();
    }
    // Update container width on every resize
    window.addEventListener('resize', updateWidth);
    return () => {
      window.removeEventListener('resize', updateWidth);
    };
  });

  if (!timestamps || timestamps.length === 0) return null;

  const handleChange = (newSelectedIndex) => {
    // when slider is on last value, we set the value to null in order to use the current state
    if (selectedIndex !== newSelectedIndex) {
      const selectedZoneTimeIndex = newSelectedIndex === (timestamps.length - 1) ? null : newSelectedIndex;
      dispatch({
        type: 'UPDATE_SLIDER_SELECTED_ZONE_TIME',
        payload: { selectedZoneTimeIndex },
      });
    }
  };

  const onChangeAndInput = (ev) => {
    const index = parseInt(ev.target.value, 10);
    setAnchoredIndex(index);
    if (handleChange) {
      handleChange(index);
    }
  };

  const timeScale = d3.scaleTime()
    .domain([first(timestamps), last(timestamps)])
    .range([0, width]);
  
  const [x1, x2] = timeScale.range();

  return (
    <div className={className}>
      <input
        type="range"
        className="time-slider-input"
        onChange={onChangeAndInput}
        onInput={onChangeAndInput}
        value={selectedIndex || anchoredIndex || timestamps.length - 1}
        max={timestamps.length - 1}
        min={0}
      />
      <svg className="time-slider-axis-container" ref={ref}>
        <g
          className="time-slider-axis"
          transform={`translate(${AXIS_MARGIN_LEFT}, 0)`}
          fill="none"
          fontSize="10"
          fontFamily="sans-serif"
          textAnchor="middle"
          style={{ pointerEvents: 'none' }}
        >
          <path className="domain" stroke="currentColor" d={`M${x1 + 0.5},6V0.5H${x2 + 0.5}V6`} />
          {sampledTickValues(timestamps).map((v, ind) => (
            <g key={`tick-${v}`} className="tick" opacity={1} transform={`translate(${timeScale(v)},0)`}>
              <line stroke="currentColor" y2="0" />
              <text fill="currentColor" y="3" dy="0.71em">{renderTick(v, ind)}</text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
};

export default connect(mapStateToProps)(TimeSlider);
