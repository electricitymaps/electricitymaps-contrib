import moment from 'moment';
import React, { useMemo, useState } from 'react';
import { connect } from 'react-redux';
import { scaleLinear } from 'd3-scale';
import { max as d3Max } from 'd3-array';

import { EMISSIONS_GRAPH_LAYER_KEY } from '../helpers/constants';
import { getCo2Scale } from '../helpers/scales';
import {
  getSelectedZoneHistory,
  getZoneHistoryStartTime,
  getZoneHistoryEndTime,
} from '../selectors';
import {
  createSingleLayerGraphBackgroundMouseMoveHandler,
  createSingleLayerGraphBackgroundMouseOutHandler,
  createGraphLayerMouseMoveHandler,
  createGraphLayerMouseOutHandler,
} from '../helpers/history';
import { tonsPerHourToGramsPerMinute } from '../helpers/math';
import { getTotalElectricity } from '../helpers/zonedata';
import { dispatchApplication } from '../store';

import CountryPanelEmissionsTooltip from './tooltips/countrypanelemissionstooltip';
import AreaGraph from './graph/areagraph';

// If in mobile mode, put the tooltip to the top of the screen for
// readability, otherwise float it depending on the cursor position.
const getTooltipPosition = (isMobile, ev) => (isMobile ? { x: 0, y: 0 } : { x: ev.clientX - 7, y: ev.clientY - 7 });

const prepareGraphData = (historyData) => {
  if (!historyData || !historyData[0]) return {};

  const data = historyData.map(d => ({
    [EMISSIONS_GRAPH_LAYER_KEY]: tonsPerHourToGramsPerMinute(getTotalElectricity(d, true)),
    datetime: moment(d.stateDatetime).toDate(),
    // Keep a pointer to original data
    meta: d,
  }));

  const maxEmissions = d3Max(data.map(d => d[EMISSIONS_GRAPH_LAYER_KEY]));
  const emissionsColorScale = scaleLinear()
    .domain([0, maxEmissions])
    .range(['yellow', 'brown']);

  const layerKeys = [EMISSIONS_GRAPH_LAYER_KEY];
  const layerFill = key => d => emissionsColorScale(d.data[key]);
  return { data, layerKeys, layerFill };
};

const mapStateToProps = state => ({
  startTime: getZoneHistoryStartTime(state),
  endTime: getZoneHistoryEndTime(state),
  historyData: getSelectedZoneHistory(state),
  isMobile: state.application.isMobile,
  selectedTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryHistoryEmissionsGraph = ({
  displayByEmissions,
  startTime,
  endTime,
  historyData,
  isMobile,
  selectedTimeIndex,
}) => {
  const [tooltip, setTooltip] = useState(null);
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill } = useMemo(
    () => prepareGraphData(historyData),
    [historyData]
  );

  // Mouse action handlers
  const mouseMoveHandler = useMemo(
    () => (timeIndex, layerIndex, getLayer, ev) => {
      dispatchApplication('selectedZoneTimeIndex', timeIndex);
      setSelectedLayerIndex(0);
      setTooltip({
        zoneData: getLayer(0).datapoints[timeIndex].data.meta,
        position: getTooltipPosition(isMobile, ev),
      });
    },
    [isMobile, setTooltip, setSelectedLayerIndex]
  );
  const mouseOutHandler = useMemo(
    () => () => {
      dispatchApplication('selectedZoneTimeIndex', null);
      setSelectedLayerIndex(null);
      setTooltip(null);
    },
    [setTooltip, setSelectedLayerIndex]
  );

  return (
    <React.Fragment>
      <AreaGraph
        data={data}
        layerKeys={layerKeys}
        layerFill={layerFill}
        startTime={startTime}
        endTime={endTime}
        valueAxisLabel="tCO2eq / min"
        backgroundMouseMoveHandler={mouseMoveHandler}
        backgroundMouseOutHandler={mouseOutHandler}
        layerMouseMoveHandler={mouseMoveHandler}
        layerMouseOutHandler={mouseOutHandler}
        selectedTimeIndex={selectedTimeIndex}
        selectedLayerIndex={selectedLayerIndex}
        isMobile={isMobile}
        height="8em"
      />
      {tooltip && (
        <CountryPanelEmissionsTooltip
          position={tooltip.position}
          zoneData={tooltip.zoneData}
        />
      )}
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(CountryHistoryEmissionsGraph);
