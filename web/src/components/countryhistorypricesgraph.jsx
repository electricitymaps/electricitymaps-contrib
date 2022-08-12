import React, { useMemo, useState } from 'react';
import { connect } from 'react-redux';
import getSymbolFromCurrency from 'currency-symbol-map';
import { max as d3Max, min as d3Min } from 'd3-array';
import { scaleLinear } from 'd3-scale';

import { getTooltipPosition } from '../helpers/graph';
import { useCurrentZoneHistory } from '../hooks/redux';

import AreaGraph from './graph/areagraph';
import PriceTooltip from './tooltips/pricetooltip';

const prepareGraphData = (historyData) => {
  if (!historyData || !historyData[0]) {
    return {};
  }

  const currencySymbol = getSymbolFromCurrency(((historyData.at(0) || {}).price || {}).currency);
  const valueAxisLabel = `${currencySymbol || '?'} / MWh`;

  const priceMaxValue = d3Max(historyData.map((d) => d.price?.value));
  const priceMinValue = d3Min(historyData.map((d) => d.price?.value));
  const priceColorScale = scaleLinear().domain([priceMinValue, priceMaxValue]).range(['lightgray', '#616161']);

  const data = historyData.map((d) => ({
    price: d.price && d.price.value,
    datetime: new Date(d.stateDatetime),
    // Keep a pointer to original data
    meta: d,
  }));

  const layerKeys = ['price'];
  const layerFill = (key) => (d) => priceColorScale(d.data[key]);
  const markerFill = (key) => (d) => priceColorScale(d.data[key]);

  return {
    data,
    layerKeys,
    layerFill,
    markerFill,
    valueAxisLabel,
  };
};

const mapStateToProps = (state) => ({
  isMobile: state.application.isMobile,
});

const CountryHistoryPricesGraph = ({ isMobile }) => {
  const [tooltip, setTooltip] = useState(null);

  const historyData = useCurrentZoneHistory();

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerStroke, layerFill, markerFill, valueAxisLabel } = useMemo(
    () => prepareGraphData(historyData),
    [historyData]
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
        testId="history-prices-graph"
        data={data}
        layerKeys={layerKeys}
        layerStroke={layerStroke}
        layerFill={layerFill}
        markerFill={markerFill}
        valueAxisLabel={valueAxisLabel}
        markerUpdateHandler={markerUpdateHandler}
        markerHideHandler={markerHideHandler}
        isMobile={isMobile}
        height="6em"
      />
      {tooltip && (
        <PriceTooltip
          position={tooltip.position}
          zoneData={tooltip.zoneData}
          onClose={() => {
            setTooltip(null);
          }}
        />
      )}
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(CountryHistoryPricesGraph);
