import getSymbolFromCurrency from 'currency-symbol-map';
import { max as d3Max, min as d3Min } from 'd3-array';
import { scaleLinear } from 'd3-scale';
import React, { useMemo, useState } from 'react';
import { ZoneDetail } from 'types';
import AreaGraph from './elements/AreaGraph';
import { getTooltipPosition, noop } from './graphUtils';

const prepareGraphData = (historyData: any) => {
  if (!historyData || !historyData[0]) {
    return {};
  }

  const currencySymbol = getSymbolFromCurrency(historyData.at(0)?.price?.currency);
  const valueAxisLabel = `${currencySymbol || '?'} / MWh`;

  const priceMaxValue = d3Max<number>(historyData.map((d: any) => d.price?.value)) || 0;
  const priceMinValue = d3Min<number>(historyData.map((d: any) => d.price?.value)) || 0;
  console.log(priceMaxValue, priceMinValue);

  const priceColorScale = scaleLinear<string>()
    .domain([priceMinValue, 0, priceMaxValue])
    .range(['brown', 'lightgray', '#616161']);

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

function PriceChart({
  electricityMixMode,
  isMobile,
  historyData,
  datetimes,
  timeAverage,
}: any) {
  // const [tooltip, setTooltip] = useState(null);

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerStroke, layerFill, markerFill, valueAxisLabel }: any =
    useMemo(() => prepareGraphData(historyData), [historyData]);

  // Graph marker callbacks
  // const markerUpdateHandler = useMemo(
  //   () => (position, datapoint) => {
  //     setTooltip({
  //       position: getTooltipPosition(isMobile, position),
  //       zoneData: datapoint.meta,
  //     });
  //   },
  //   [setTooltip, isMobile]
  // );
  // const markerHideHandler = useMemo(
  //   () => () => {
  //     setTooltip(null);
  //   },
  //   [setTooltip]
  // );

  return (
    <div className="ml-3">
      <AreaGraph
        testId="history-prices-graph"
        data={data}
        layerKeys={layerKeys}
        layerStroke={layerStroke}
        layerFill={layerFill}
        markerFill={markerFill}
        valueAxisLabel={valueAxisLabel}
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        isMobile={isMobile}
        height="6em"
        datetimes={datetimes}
        selectedTimeAggregate={timeAverage}
        selectedZoneTimeIndex={0}
        isOverlayEnabled={false}
      />
      {/* {tooltip && (
        <PriceTooltip
          position={tooltip.position}
          zoneData={tooltip.zoneData}
          onClose={() => {
            setTooltip(null);
          }}
        />
      )} */}
    </div>
  );
}

export default PriceChart;
