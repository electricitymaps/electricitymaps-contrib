import React, { useMemo, useState } from 'react';
import { connect } from 'react-redux';
//@ts-ignore
import getSymbolFromCurrency from 'currency-symbol-map';
import { max as d3Max, min as d3Min } from 'd3-array';
import { scaleLinear } from 'd3-scale';

import { getTooltipPosition } from '../helpers/graph';
import { useCurrentZoneHistory } from '../hooks/redux';

import AreaGraph from './graph/areagraph';
import PriceTooltip from './tooltips/pricetooltip';

const prepareGraphData = (historyData: any) => {
  if (!historyData || !historyData[0]) {
    return {};
  }

  const currencySymbol = getSymbolFromCurrency(historyData.at(0)?.price?.currency);
  const valueAxisLabel = `${currencySymbol || '?'} / MWh`;

  const priceMaxValue = d3Max(historyData.map((d: any) => d.price?.value));
  const priceMinValue = d3Min(historyData.map((d: any) => d.price?.value));
  //@ts-ignore
  const priceColorScale = scaleLinear().domain([priceMinValue, priceMaxValue]).range(['lightgray', '#616161']);

  const data = historyData.map((d: any) => ({
    price: d.price && d.price.value,
    datetime: new Date(d.stateDatetime),

    // Keep a pointer to original data
    meta: d,
  }));

  const layerKeys = ['price'];
  const layerFill = (key: any) => (d: any) => priceColorScale(d.data[key]);
  const markerFill = (key: any) => (d: any) => priceColorScale(d.data[key]);

  return {
    data,
    layerKeys,
    layerFill,
    markerFill,
    valueAxisLabel,
  };
};

const mapStateToProps = (state: any) => ({
  isMobile: state.application.isMobile,
});

const CountryHistoryPricesGraph = ({ isMobile }: any) => {
  const [tooltip, setTooltip] = useState(null);

  const historyData = useCurrentZoneHistory();

  // Recalculate graph data only when the history data is changed
  // @ts-expect-error TS(2339): Property 'layerStroke' does not exist on type '{ d... Remove this comment to see the full error message
  const { data, layerKeys, layerStroke, layerFill, markerFill, valueAxisLabel } = useMemo(
    () => prepareGraphData(historyData),
    [historyData]
  );

  // Graph marker callbacks
  const markerUpdateHandler = useMemo(
    () => (position: any, datapoint: any) => {
      setTooltip({
        // @ts-expect-error TS(2345): Argument of type '{ position: any; zoneData: any; ... Remove this comment to see the full error message
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
          position={(tooltip as any).position}
          zoneData={(tooltip as any).zoneData}
          onClose={() => {
            setTooltip(null);
          }}
        />
      )}
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(CountryHistoryPricesGraph);
