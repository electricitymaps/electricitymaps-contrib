import moment from 'moment';
import React, { useMemo, useState } from 'react';
import { connect, useSelector } from 'react-redux';
import getSymbolFromCurrency from 'currency-symbol-map';
import { max as d3Max } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import { first } from 'lodash';

import { getTooltipPosition } from '../helpers/graph';
import { dispatchApplication } from '../store';
import {
  useCurrentZoneHistory,
  useCurrentZoneHistoryStartTime,
  useCurrentZoneHistoryEndTime,
} from '../hooks/redux';

import AreaGraph from './graph/areagraph';
import PriceTooltip from './tooltips/pricetooltip';

const prepareGraphData = (historyData, electricityMixMode) => {
  if (!historyData || !historyData[0]) return {};

  const currencySymbol = getSymbolFromCurrency(((first(historyData) || {}).price || {}).currency);
  const valueAxisLabel = `${currencySymbol || '?'} / MWh`;

  const priceMaxValue = d3Max(historyData.map(d => (d.price || {}).value));
  const priceColorScale = scaleLinear()
    .domain([0, priceMaxValue])
    .range(['yellow', 'red']);

  const data = historyData.map(d => ({
    price: d.price && d.price.value,
    datetime: moment(d.stateDatetime).toDate(),
    // Keep a pointer to original data
    meta: d,
  }));

  const layerKeys = ['price'];
  const layerStroke = () => 'darkgray';
  const layerFill = () => '#616161';
  const markerFill = key => d => priceColorScale(d.data[key]);

  return {
    data,
    layerKeys,
    layerStroke,
    layerFill,
    markerFill,
    valueAxisLabel,
  };
};

const mapStateToProps = state => ({
  electricityMixMode: state.application.electricityMixMode,
  isMobile: state.application.isMobile,
  selectedTimeIndex: state.application.selectedZoneTimeIndex,
});

const CountryHistoryPricesGraph = ({
  electricityMixMode,
  isMobile,
  selectedTimeIndex,
}) => {
  const [tooltip, setTooltip] = useState(null);
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);

  const historyData = useCurrentZoneHistory();
  const startTime = useCurrentZoneHistoryStartTime();
  const endTime = useCurrentZoneHistoryEndTime();

  // Recalculate graph data only when the history data is changed
  const {
    data,
    layerKeys,
    layerStroke,
    layerFill,
    markerFill,
    valueAxisLabel,
  } = useMemo(
    () => prepareGraphData(historyData, electricityMixMode),
    [historyData, electricityMixMode]
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
        layerStroke={layerStroke}
        layerFill={layerFill}
        markerFill={markerFill}
        startTime={startTime}
        endTime={endTime}
        valueAxisLabel={valueAxisLabel}
        backgroundMouseMoveHandler={mouseMoveHandler}
        backgroundMouseOutHandler={mouseOutHandler}
        layerMouseMoveHandler={mouseMoveHandler}
        layerMouseOutHandler={mouseOutHandler}
        markerUpdateHandler={markerUpdateHandler}
        markerHideHandler={markerHideHandler}
        selectedTimeIndex={selectedTimeIndex}
        selectedLayerIndex={selectedLayerIndex}
        isMobile={isMobile}
        height="6em"
      />
      {tooltip && (
        <PriceTooltip
          position={tooltip.position}
          zoneData={tooltip.zoneData}
        />
      )}
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(CountryHistoryPricesGraph);
