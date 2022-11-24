import { max as d3Max } from 'd3-array';
import { useCo2ColorScale } from 'hooks/theme';
import { useMemo } from 'react';
import { ZoneDetail } from 'types';
import { modeColor, modeOrder, TimeAverages } from 'utils/constants';
import { scalePower } from 'utils/formatting';
import AreaGraph from './elements/AreaGraph';
import { getGenerationTypeKey, getStorageKey, noop } from './graphUtils';

interface ValuesInfo {
  valueAxisLabel: string; // For example, GW or tCO₂eq/min
  valueFactor: number; // TODO: why is this required
}

const getValuesInfo = (
  historyData: ZoneDetail[],
  displayByEmissions: boolean
): ValuesInfo => {
  const maxTotalValue = d3Max(
    historyData,
    (d: ZoneDetail) =>
      displayByEmissions
        ? (d.totalCo2Production + d.totalCo2Import + d.totalCo2Discharge) / 1e6 / 60 // in tCO₂eq/min
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
  exchangeKeys: string[]
) => {
  if (!historyData || !historyData[0]) {
    return {};
  }

  const { valueAxisLabel, valueFactor } = getValuesInfo(historyData, displayByEmissions);

  // Format history data received by the API
  // TODO: Simplify this function and make it more readable
  // TODO (mk): We should assume that this data is already more typed and we don't need
  // all these checks
  const data = historyData.map((d: any) => {
    const object: any = {
      datetime: new Date(d.stateDatetime),
      meta: {},
    };

    const hasProductionData =
      d.production && Object.values(d.production).some((v) => v !== null);
    if (hasProductionData) {
      // Add production
      for (const k of modeOrder) {
        const isStorage = k.includes('storage');
        let value = undefined;
        if (isStorage) {
          const storageKey = getStorageKey(k);
          if (storageKey !== undefined) {
            value = -1 * Math.min(0, (d.storage || {})[storageKey]);
          }
        } else {
          const generationKey = getGenerationTypeKey(k);
          if (generationKey !== undefined) {
            value = (d.production || {})[generationKey];
          }
        }

        // in GW or MW
        object[k] = value !== undefined ? value / valueFactor : undefined;
        if (Number.isFinite(value) && displayByEmissions && object[k] != undefined) {
          // in tCO₂eq/min
          if (isStorage && object[k] >= 0) {
            object[k] *=
              (d.dischargeCo2Intensities || {})[k.replace(' storage', '')] / 1e3 / 60;
          } else {
            object[k] *= (d.productionCo2Intensities || {})[k] / 1e3 / 60;
          }
        }
      }

      if (electricityMixMode === 'consumption') {
        // Add exchange
        for (const [key, value] of Object.entries(d.exchange)) {
          const value_: number = value as number;
          // in GW or MW
          object[key] = Math.max(0, value_ / valueFactor);
          if (Number.isFinite(value) && displayByEmissions && object[key] != undefined) {
            // in tCO₂eq/min
            object[key] *= (d.exchangeCo2Intensities || {})[key] / 1e3 / 60;
          }
        }
      }
    }

    // Keep a pointer to original data
    object.meta = d;
    return object;
  });

  // Show the exchange layers (if they exist) on top of the standard sources.
  const layerKeys = [...modeOrder, ...exchangeKeys];

  const layerFill = (key: string) => {
    // If exchange layer, set the horizontal gradient by using a different fill for each datapoint.
    if (exchangeKeys.includes(key)) {
      return (d: any) => co2ColorScale((d.data.meta.exchangeCo2Intensities || {})[key]);
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

interface BreakdownChartProps {
  displayByEmissions: boolean;
  electricityMixMode: string;
  isMobile: boolean;
  isOverlayEnabled: boolean;
  historyData: any;
  exchangeKeys: string[];
  datetimes: Date[];
  timeAverage: TimeAverages;
}

function BreakdownChart({
  displayByEmissions,
  electricityMixMode,
  isMobile,
  isOverlayEnabled,
  historyData,
  exchangeKeys,
  datetimes,
  timeAverage,
}: BreakdownChartProps) {
  // const [tooltip, setTooltip] = useState(null);
  const co2ColorScale = useCo2ColorScale();

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill, valueAxisLabel } = useMemo(
    () =>
      prepareGraphData(
        historyData,
        co2ColorScale,
        displayByEmissions,
        electricityMixMode,
        exchangeKeys
      ),
    [historyData, co2ColorScale, displayByEmissions, electricityMixMode, exchangeKeys]
  );

  // Graph marker callbacks
  // const markerUpdateHandler = useMemo(
  //   () => (position, datapoint, layerKey) => {
  //     setTooltip({
  //       mode: layerKey,
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
        testId="history-mix-graph"
        data={data}
        layerKeys={layerKeys}
        layerFill={layerFill}
        valueAxisLabel={valueAxisLabel}
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        isMobile={isMobile}
        height="10em"
        isOverlayEnabled={isOverlayEnabled}
        datetimes={datetimes}
        selectedTimeAggregate={timeAverage}
        selectedZoneTimeIndex={0}
      />
      {/* {tooltip &&
        (exchangeKeys.includes(tooltip.mode) ? (
          <CountryPanelExchangeTooltip
            exchangeKey={tooltip.mode}
            position={tooltip.position}
            zoneData={tooltip.zoneData}
            onClose={() => {
              setTooltip(null);
            }}
          />
        ) : (
          <CountryPanelProductionTooltip
            mode={tooltip.mode}
            position={tooltip.position}
            zoneData={tooltip.zoneData}
            onClose={() => {
              setTooltip(null);
            }}
          />
        ))} */}
    </div>
  );
}

// export default connect(mapStateToProps)(CountryHistoryMixGraph);
export default BreakdownChart;
