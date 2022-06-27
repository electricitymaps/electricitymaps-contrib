import React, { useState, useMemo } from 'react';
import { connect } from 'react-redux';
import { max as d3Max } from 'd3-array';

import { scalePower } from '../helpers/formatting';
import { useCo2ColorScale } from '../hooks/theme';
import { getTooltipPosition } from '../helpers/graph';
import { modeOrder, modeColor } from '../helpers/constants';
import { useCurrentZoneHistory, useCurrentZoneExchangeKeys, useCurrentZoneHistoryDatetimes } from '../hooks/redux';

import CountryPanelProductionTooltip from './tooltips/countrypanelproductiontooltip';
import CountryPanelExchangeTooltip from './tooltips/countrypanelexchangetooltip';
import AreaGraph from './graph/areagraph';

const getValuesInfo = (historyData, displayByEmissions) => {
  const maxTotalValue = d3Max(
    historyData,
    (d) =>
      displayByEmissions
        ? (d.totalCo2Production + d.totalCo2Import + d.totalCo2Discharge) / 1e6 / 60.0 // in tCO₂eq/min
        : d.totalProduction + d.totalImport + d.totalDischarge // in MW
  );
  const format = scalePower(maxTotalValue);

  const valueAxisLabel = displayByEmissions ? 'tCO₂eq / min' : format.unit;
  const valueFactor = format.formattingFactor;
  return { valueAxisLabel, valueFactor };
};

const prepareGraphData = (historyData, co2ColorScale, displayByEmissions, electricityMixMode, exchangeKeys) => {
  if (!historyData || !historyData[0]) {
    return {};
  }

  const { valueAxisLabel, valueFactor } = getValuesInfo(historyData, displayByEmissions);

  // Format history data received by the API
  // TODO: Simplify this function and make it more readable
  const data = historyData.map((d) => {
    const obj = {
      datetime: new Date(d.stateDatetime),
    };

    const hasProductionData = d.production && Object.values(d.production).some((v) => v !== null);

    if (hasProductionData) {
      // Add production
      modeOrder.forEach((k) => {
        const isStorage = k.indexOf('storage') !== -1;
        let value = isStorage
          ? -1 * Math.min(0, (d.storage || {})[k.replace(' storage', '')])
          : (d.production || {})[k];

        if (value === null) {
          value = undefined;
        }

        // in GW or MW
        obj[k] = value / valueFactor;
        if (Number.isFinite(value) && displayByEmissions && obj[k] != null) {
          // in tCO₂eq/min
          if (isStorage && obj[k] >= 0) {
            obj[k] *= (d.dischargeCo2Intensities || {})[k.replace(' storage', '')] / 1e3 / 60.0;
          } else {
            obj[k] *= (d.productionCo2Intensities || {})[k] / 1e3 / 60.0;
          }
        }
      });

      if (electricityMixMode === 'consumption') {
        // Add exchange
        Object.entries(d.exchange).forEach(([key, value]) => {
          // in GW or MW
          obj[key] = Math.max(0, value / valueFactor);
          if (Number.isFinite(value) && displayByEmissions && obj[key] != null) {
            // in tCO₂eq/min
            obj[key] *= (d.exchangeCo2Intensities || {})[key] / 1e3 / 60.0;
          }
        });
      }
    }

    // Keep a pointer to original data
    obj.meta = d;
    return obj;
  });

  // Show the exchange layers (if they exist) on top of the standard sources.
  const layerKeys = modeOrder.concat(exchangeKeys);

  const layerFill = (key) => {
    // If exchange layer, set the horizontal gradient by using a different fill for each datapoint.
    if (exchangeKeys.includes(key)) {
      return (d) => co2ColorScale((d.data.meta.exchangeCo2Intensities || {})[key]);
    }
    // Otherwise use regular production fill.
    return modeColor[key];
  };

  return {
    data,
    layerKeys,
    layerFill,
    valueAxisLabel,
  };
};

const mapStateToProps = (state) => ({
  displayByEmissions: state.application.tableDisplayEmissions,
  electricityMixMode: state.application.electricityMixMode,
  isMobile: state.application.isMobile,
});

const CountryHistoryMixGraph = ({ displayByEmissions, electricityMixMode, isMobile }) => {
  const [graphIndex, setGraphIndex] = useState(null);
  const [tooltip, setTooltip] = useState(null);
  const [selectedLayerIndex, setSelectedLayerIndex] = useState(null);
  const co2ColorScale = useCo2ColorScale();

  const historyData = useCurrentZoneHistory();
  const exchangeKeys = useCurrentZoneExchangeKeys();
  const datetimes = useCurrentZoneHistoryDatetimes();
  const startTime = datetimes.at(0);
  const endTime = datetimes.at(-1);

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill, valueAxisLabel } = useMemo(
    () => prepareGraphData(historyData, co2ColorScale, displayByEmissions, electricityMixMode, exchangeKeys),
    [historyData, co2ColorScale, displayByEmissions, electricityMixMode, exchangeKeys]
  );

  // Mouse action handlers
  const backgroundMouseMoveHandler = useMemo(
    () => (timeIndex) => {
      setGraphIndex(timeIndex);
    },
    []
  );
  const backgroundMouseOutHandler = useMemo(
    () => () => {
      setGraphIndex(null);
    },
    []
  );
  const layerMouseMoveHandler = useMemo(
    () => (timeIndex, layerIndex) => {
      setGraphIndex(timeIndex);
      setSelectedLayerIndex(layerIndex);
    },
    [setSelectedLayerIndex]
  );
  const layerMouseOutHandler = useMemo(
    () => () => {
      setGraphIndex(null);
      setSelectedLayerIndex(null);
    },
    [setSelectedLayerIndex]
  );
  // Graph marker callbacks
  const markerUpdateHandler = useMemo(
    () => (position, datapoint, layerKey) => {
      setTooltip({
        mode: layerKey,
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
        testId="history-mix-graph"
        data={data}
        layerKeys={layerKeys}
        layerFill={layerFill}
        startTime={startTime}
        endTime={endTime}
        valueAxisLabel={valueAxisLabel}
        backgroundMouseMoveHandler={backgroundMouseMoveHandler}
        backgroundMouseOutHandler={backgroundMouseOutHandler}
        layerMouseMoveHandler={layerMouseMoveHandler}
        layerMouseOutHandler={layerMouseOutHandler}
        markerUpdateHandler={markerUpdateHandler}
        markerHideHandler={markerHideHandler}
        selectedTimeIndex={graphIndex}
        selectedLayerIndex={selectedLayerIndex}
        isMobile={isMobile}
        height="10em"
      />
      {tooltip &&
        (exchangeKeys.includes(tooltip.mode) ? (
          <CountryPanelExchangeTooltip
            exchangeKey={tooltip.mode}
            position={tooltip.position}
            zoneData={tooltip.zoneData}
            onClose={() => {
              setSelectedLayerIndex(null);
              setTooltip(null);
            }}
          />
        ) : (
          <CountryPanelProductionTooltip
            mode={tooltip.mode}
            position={tooltip.position}
            zoneData={tooltip.zoneData}
            onClose={() => {
              setSelectedLayerIndex(null);
              setTooltip(null);
            }}
          />
        ))}
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(CountryHistoryMixGraph);
