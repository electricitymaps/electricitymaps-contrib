import moment from 'moment';
import React, { useMemo, useState } from 'react';
import { connect, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { scaleLinear } from 'd3-scale';
import { max as d3Max } from 'd3-array';

import { getTooltipPosition } from '../helpers/graph';
import { useCustomDatetime } from '../helpers/router';
import { getCo2Scale } from '../helpers/scales';
import {
  getZoneHistory,
  getZoneHistoryStartTime,
  getZoneHistoryEndTime,
} from '../selectors';
import { tonsPerHourToGramsPerMinute } from '../helpers/math';
import { getTotalElectricity } from '../helpers/zonedata';
import { dispatchApplication } from '../store';

import CountryPanelEmissionsTooltip from './tooltips/countrypanelemissionstooltip';
import AreaGraph from './graph/areagraph';

const prepareGraphData = (historyData) => {
  if (!historyData || !historyData[0]) return {};

  const data = historyData.map(d => ({
    emissions: tonsPerHourToGramsPerMinute(getTotalElectricity(d, true)),
    datetime: moment(d.stateDatetime).toDate(),
    // Keep a pointer to original data
    meta: d,
  }));

  const maxEmissions = d3Max(data.map(d => d.emissions));
  const emissionsColorScale = scaleLinear()
    .domain([0, maxEmissions])
    .range(['yellow', 'brown']);

  const layerKeys = ['emissions'];
  const layerFill = key => d => emissionsColorScale(d.data[key]);
  return { data, layerKeys, layerFill };
};

const mapStateToProps = state => ({
  isMobile: state.application.isMobile,
  selectedTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryHistoryEmissionsGraph = ({
  isMobile,
  selectedTimeIndex,
}) => {
  const [tooltip, setTooltip] = useState(null);
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);

  const { zoneId } = useParams();
  const historyData = useSelector(getZoneHistory(zoneId));

  const customDatetime = useCustomDatetime();
  const startTime = useSelector(getZoneHistoryStartTime(customDatetime));
  const endTime = useSelector(getZoneHistoryEndTime(customDatetime));

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill } = useMemo(
    () => prepareGraphData(historyData),
    [historyData]
  );

  // Mouse action handlers
  const mouseMoveHandler = useMemo(
    () => (timeIndex) => {
      dispatchApplication('selectedZoneTimeIndex', timeIndex);
      setSelectedLayerIndex(0); // Select the first (and only) layer even when hovering over graph background.
    },
    [setSelectedLayerIndex]
  );
  const mouseOutHandler = useMemo(
    () => () => {
      dispatchApplication('selectedZoneTimeIndex', null);
      setSelectedLayerIndex(null);
    },
    [setSelectedLayerIndex]
  );
  // Graph marker callbacks
  const markerUpdateHandler = useMemo(
    () => (position, datapoint) => {
      setTooltip({
        position: getTooltipPosition(isMobile, position),
        zoneData: datapoint.meta,
      });
    },
    [setTooltip, isMobile]
  );
  const markerHideHandler = useMemo(
    () => () => {
      setTooltip(null);
    },
    [setTooltip]
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
        markerUpdateHandler={markerUpdateHandler}
        markerHideHandler={markerHideHandler}
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
