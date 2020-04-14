import moment from 'moment';
import React, { useMemo, useState } from 'react';
import { connect, useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';

import { getTooltipPosition } from '../helpers/graph';
import { useCustomDatetime } from '../helpers/router';
import { getCo2Scale } from '../helpers/scales';
import {
  getZoneHistorySelector,
  getZoneHistoryStartTimeSelector,
  getZoneHistoryEndTimeSelector,
} from '../selectors/redux';
import { dispatchApplication } from '../store';

import MapCountryTooltip from './tooltips/mapcountrytooltip';
import AreaGraph from './graph/areagraph';

const prepareGraphData = (historyData, colorBlindModeEnabled, electricityMixMode) => {
  if (!historyData || !historyData[0]) return {};

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const data = historyData.map(d => ({
    carbonIntensity: electricityMixMode === 'consumption'
      ? d.co2intensity
      : d.co2intensityProduction,
    datetime: moment(d.stateDatetime).toDate(),
    // Keep a pointer to original data
    meta: d,
  }));
  const layerKeys = ['carbonIntensity'];
  const layerFill = key => d => co2ColorScale(d.data[key]);
  return { data, layerKeys, layerFill };
};

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  electricityMixMode: state.application.electricityMixMode,
  isMobile: state.application.isMobile,
  selectedTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryHistoryCarbonGraph = ({
  colorBlindModeEnabled,
  electricityMixMode,
  isMobile,
  selectedTimeIndex,
}) => {
  const [tooltip, setTooltip] = useState(null);
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);

  const { zoneId } = useParams();
  const historyData = useSelector(getZoneHistorySelector(zoneId));

  const customDatetime = useCustomDatetime();
  const startTime = useSelector(getZoneHistoryStartTimeSelector(customDatetime));
  const endTime = useSelector(getZoneHistoryEndTimeSelector(customDatetime));

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill } = useMemo(
    () => prepareGraphData(historyData, colorBlindModeEnabled, electricityMixMode),
    [historyData, colorBlindModeEnabled, electricityMixMode]
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
        valueAxisLabel="g / kWh"
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
        <MapCountryTooltip
          position={tooltip.position}
          zoneData={tooltip.zoneData}
        />
      )}
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(CountryHistoryCarbonGraph);
