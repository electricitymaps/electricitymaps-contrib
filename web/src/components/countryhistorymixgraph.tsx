import React, { useState, useMemo } from 'react';
import { connect } from 'react-redux';
import { max as d3Max } from 'd3-array';

import { scalePower } from '../helpers/formatting';
import { useCo2ColorScale } from '../hooks/theme';
import { getTooltipPosition } from '../helpers/graph';
import { modeOrder, modeColor } from '../helpers/constants';
import { useCurrentZoneHistory, useCurrentZoneExchangeKeys } from '../hooks/redux';

import CountryPanelProductionTooltip from './tooltips/countrypanelproductiontooltip';
import CountryPanelExchangeTooltip from './tooltips/countrypanelexchangetooltip';
import AreaGraph from './graph/areagraph';

const getValuesInfo = (historyData: any, displayByEmissions: any) => {
  const maxTotalValue = d3Max(
    historyData,
    (d: any) =>
      displayByEmissions
        ? (d.totalCo2Production + d.totalCo2Import + d.totalCo2Discharge) / 1e6 / 60.0 // in tCO₂eq/min
        : d.totalProduction + d.totalImport + d.totalDischarge // in MW
  );
  const format = scalePower(maxTotalValue);

  const valueAxisLabel = displayByEmissions ? 'tCO₂eq / min' : format.unit;
  const valueFactor = format.formattingFactor;
  return { valueAxisLabel, valueFactor };
};

const prepareGraphData = (
  historyData: any,
  co2ColorScale: any,
  displayByEmissions: any,
  electricityMixMode: any,
  exchangeKeys: any
) => {
  if (!historyData || !historyData[0]) {
    return {};
  }

  const { valueAxisLabel, valueFactor } = getValuesInfo(historyData, displayByEmissions);

  // Format history data received by the API
  // TODO: Simplify this function and make it more readable
  const data = historyData.map((d: any) => {
    const obj = {
      datetime: new Date(d.stateDatetime),
    };

    const hasProductionData = d.production && Object.values(d.production).some((v: any) => v !== null);

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
        // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
        obj[k] = value / valueFactor;
        // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
        if (Number.isFinite(value) && displayByEmissions && obj[k] != null) {
          // in tCO₂eq/min
          // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
          if (isStorage && obj[k] >= 0) {
            // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
            obj[k] *= (d.dischargeCo2Intensities || {})[k.replace(' storage', '')] / 1e3 / 60.0;
          } else {
            // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
            obj[k] *= (d.productionCo2Intensities || {})[k] / 1e3 / 60.0;
          }
        }
      });

      if (electricityMixMode === 'consumption') {
        // Add exchange

        Object.entries(d.exchange).forEach(([key, value]) => {
          // in GW or MW
          // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
          obj[key] = Math.max(0, value / valueFactor);
          // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
          if (Number.isFinite(value) && displayByEmissions && obj[key] != null) {
            // in tCO₂eq/min
            // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
            obj[key] *= (d.exchangeCo2Intensities || {})[key] / 1e3 / 60.0;
          }
        });
      }
    }

    // Keep a pointer to original data
    (obj as any).meta = d;
    return obj;
  });

  // Show the exchange layers (if they exist) on top of the standard sources.
  const layerKeys = modeOrder.concat(exchangeKeys);

  const layerFill = (key: any) => {
    // If exchange layer, set the horizontal gradient by using a different fill for each datapoint.
    if (exchangeKeys.includes(key)) {
      return (d: any) => co2ColorScale((d.data.meta.exchangeCo2Intensities || {})[key]);
    }
    // Otherwise use regular production fill.
    // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    return modeColor[key];
  };

  return {
    data,
    layerKeys,
    layerFill,
    valueAxisLabel,
  };
};

const mapStateToProps = (state: any) => ({
  displayByEmissions: state.application.tableDisplayEmissions,
  electricityMixMode: state.application.electricityMixMode,
  isMobile: state.application.isMobile,
});

const CountryHistoryMixGraph = ({ displayByEmissions, electricityMixMode, isMobile, isOverlayEnabled }: any) => {
  const [tooltip, setTooltip] = useState(null);
  const co2ColorScale = useCo2ColorScale();

  const historyData = useCurrentZoneHistory();
  const exchangeKeys = useCurrentZoneExchangeKeys();

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill, valueAxisLabel } = useMemo(
    () => prepareGraphData(historyData, co2ColorScale, displayByEmissions, electricityMixMode, exchangeKeys),
    [historyData, co2ColorScale, displayByEmissions, electricityMixMode, exchangeKeys]
  );

  // Graph marker callbacks
  const markerUpdateHandler = useMemo(
    () => (position: any, datapoint: any, layerKey: any) => {
      setTooltip({
        // @ts-expect-error TS(2345): Argument of type '{ mode: any; position: any; zone... Remove this comment to see the full error message
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
        valueAxisLabel={valueAxisLabel}
        markerUpdateHandler={markerUpdateHandler}
        markerHideHandler={markerHideHandler}
        isMobile={isMobile}
        height="10em"
        isOverlayEnabled={isOverlayEnabled}
      />
      {tooltip &&
        (exchangeKeys.includes((tooltip as any).mode) ? (
          <CountryPanelExchangeTooltip
            exchangeKey={(tooltip as any).mode}
            position={(tooltip as any).position}
            zoneData={(tooltip as any).zoneData}
            onClose={() => {
              setTooltip(null);
            }}
          />
        ) : (
          <CountryPanelProductionTooltip
            mode={(tooltip as any).mode}
            position={(tooltip as any).position}
            zoneData={(tooltip as any).zoneData}
            onClose={() => {
              setTooltip(null);
            }}
          />
        ))}
    </React.Fragment>
  );
};

export default connect(mapStateToProps)(CountryHistoryMixGraph);
