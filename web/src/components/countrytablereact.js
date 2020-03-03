import React, { useRef, useEffect, useState } from 'react';
import { connect } from 'react-redux';
import { scaleLinear } from 'd3-scale';
import { max as d3Max } from 'd3-array';
import { isFinite } from 'lodash';

import { getCo2Scale } from '../helpers/scales';
import { modeOrder, modeColor } from '../helpers/constants';
import { getSelectedZoneExchangeKeys } from '../helpers/history';
import { getCurrentZoneData } from '../helpers/redux';
import { __ } from '../helpers/translation';

const LABEL_MAX_WIDTH = 102;
const TEXT_ADJUST_Y = 11;
const ROW_HEIGHT = 13;
const PADDING_Y = 7;
const PADDING_X = 5;

const getSortedProductionData = data => modeOrder
  .map(k => ({ 'mode': k, 'isStorage': k.indexOf('storage') !== -1 }))
  .map((d) => {
    let footprint;
    let storage = d.isStorage ? (data.storage || {})[d.mode.replace(' storage', '')] : undefined;
    const production = !d.isStorage ? (data.production || {})[d.mode] : undefined;
    if (d.isStorage) {
      storage = (data.storage || {})[d.mode.replace(' storage', '')];
      if (storage > 0) {
        // Storage
        footprint = (data.storageCo2Intensities || {})[d.mode.replace(' storage', '')];
      } else {
        // Discharge
        // if (this._data.dischargeCo2Intensities) { debugger }
        footprint = (data.dischargeCo2Intensities || {})[d.mode.replace(' storage', '')];
      }
    } else {
      footprint = (data.productionCo2Intensities || {})[d.mode];
    }
    const capacity = (data.capacity || {})[d.mode];
    return {
      production,
      storage,
      isStorage: d.isStorage,
      capacity,
      mode: d.mode,
      text: __(d.mode),
      gCo2eqPerkWh: footprint,
      gCo2eqPerH: footprint * 1000.0 * Math.max(d.isStorage ? Math.abs(storage) : production, 0),
    };
  });

const mapStateToProps = state => ({
  colorBlindModeEnabled: state.application.colorBlindModeEnabled,
  displayByEmissions: state.application.tableDisplayEmissions,
  data: getCurrentZoneData(state),
  electricityMixMode: state.application.electricityMixMode,
  exchangeKeys: getSelectedZoneExchangeKeys(state),
});

const CountryTable = ({
  colorBlindModeEnabled,
  data,
  displayByEmissions,
  electricityMixMode,
  exchangeKeys,
}) => {
  const ref = useRef(null);
  const [containerWidth, setContainerWidth] = useState(0);

  // Container resize hook
  useEffect(() => {
    const updateContainerWidth = () => {
      if (ref.current) {
        setContainerWidth(ref.current.getBoundingClientRect().width);
      }
    };
    // Initialize width if it's not set yet
    if (!containerWidth) {
      updateContainerWidth();
    }
    // Update container width on every resize
    window.addEventListener('resize', updateContainerWidth);
    return () => {
      window.removeEventListener('resize', updateContainerWidth);
    };
  });

  const exchangeData = [];

  const co2ColorScale = getCo2Scale(colorBlindModeEnabled);
  const sortedProductionData = getSortedProductionData(data);
  const barMaxWidth = containerWidth - LABEL_MAX_WIDTH - PADDING_X;

  const getExchangeCo2eq = (d) => {
    const co2intensity = electricityMixMode === 'consumption'
      ? data.co2intensity
      : data.co2intensityProduction;
    const { exchangeCo2Intensities } = data;
    return d.value > 0
      ? ((exchangeCo2Intensities !== undefined && exchangeCo2Intensities[d.key] !== undefined)
        ? exchangeCo2Intensities[d.key]
        : undefined)
      : ((co2intensity !== undefined) ? co2intensity : undefined);
  };

  const powerScale = scaleLinear()
    .domain([
      Math.min(
        -data.maxStorageCapacity || 0,
        -data.maxStorage || 0,
        -data.maxExport || 0,
        -data.maxExportCapacity || 0
      ),
      Math.max(
        data.maxCapacity || 0,
        data.maxProduction || 0,
        data.maxDischarge || 0,
        data.maxStorageCapacity || 0,
        data.maxImport || 0,
        data.maxImportCapacity || 0
      ),
    ])
    .range([0, barMaxWidth]);

  const maxCO2eqExport = d3Max(exchangeData, (d) => {
    const co2intensity = electricityMixMode === 'consumption'
      ? data.co2intensity
      : data.co2intensityProduction;
    return d.value >= 0 ? 0 : (data.co2intensity / 1e3 * -d.value / 60.0 || 0);
  });
  const maxCO2eqImport = d3Max(exchangeData, (d) => {
    const { exchangeCo2Intensities } = data;
    if (!exchangeCo2Intensities) return 0;
    return d.value <= 0 ? 0 : exchangeCo2Intensities[d.key] / 1e3 * d.value / 60.0;
  });
  
  const co2Scale = scaleLinear() // in tCO2eq/min
    .domain([
      -maxCO2eqExport || 0,
      Math.max(
        d3Max(sortedProductionData, d => d.gCo2eqPerH / 1e6 / 60.0) || 0,
        maxCO2eqImport || 0
      ),
    ])
    .range([0, barMaxWidth]);

  return (
    <div className="country-table-container">
      <svg className="country-table" height="382" ref={ref}>
        <g />
        <g transform="translate(0,22)">
          {sortedProductionData.map((d, ind) => {
            // const showUnknown = displayByEmissions && getExchangeCo2eq(d) === undefined;
            const showUnknown = (d.capacity === undefined || d.capacity > 0)
              && d.mode !== 'unknown'
              && (d.isStorage ? d.storage === undefined : d.production === undefined);
            const productionXValue = (!d.isStorage) ? d.production : -1 * d.storage;
            const productionWidthValue = d.production !== undefined ? d.production : -1 * d.storage;
            const capacityXValue = ((data.exchangeCapacities || {})[d.key] || [])[0];
            const capacityWidthValue = (data.exchangeCapacities || {})[d.key];
            return (
              <g key={d.mode} className="row" transform={`translate(0, ${ind * (ROW_HEIGHT + PADDING_Y)})`}>
                <text
                  className="name"
                  style={{ textAnchor: 'end' }}
                  transform={`translate(${LABEL_MAX_WIDTH - 1.5 * PADDING_Y}, ${TEXT_ADJUST_Y})`}
                >
                  {__(d.mode) || d.mode}
                </text>
                {!displayByEmissions && (
                  <rect
                    className="capacity"
                    height={ROW_HEIGHT}
                    fillOpacity="0.4"
                    opacity="0.3"
                    shapeRendering="crispEdges"
                    x={LABEL_MAX_WIDTH + ((capacityXValue === undefined || !isFinite(capacityXValue)) ? powerScale(0) : powerScale(Math.min(0, capacityXValue)))}
                    // width={capacityWidthValue ? (powerScale(capacityWidthValue[1] - capacityWidthValue[0]) - powerScale(0)) : 0}
                    width={
                      d.capacity !== undefined && d.capacity >= (d.production || 0)
                        ? (powerScale(d.isStorage ? (d.capacity * 2) : d.capacity) - powerScale(0))
                        : 0
                    }
                  />
                )}
                <rect
                  className="production"
                  height={ROW_HEIGHT}
                  opacity="0.8"
                  shapeRendering="crispEdges"
                  fill={modeColor[d.mode]}
                  x={
                    displayByEmissions
                      ? LABEL_MAX_WIDTH + co2Scale(0)
                      : LABEL_MAX_WIDTH + ((productionXValue === undefined || !isFinite(productionXValue)) ? powerScale(0) : powerScale(Math.min(0, productionXValue)))
                  }
                  width={
                    displayByEmissions
                      ? (!isFinite(d.gCo2eqPerH) ? 0 : (co2Scale(d.gCo2eqPerH / 1e6 / 60.0) - co2Scale(0)))
                      : (productionWidthValue === undefined || !isFinite(productionWidthValue)) ? 0 : Math.abs(powerScale(productionWidthValue) - powerScale(0))
                  }
                />
                {showUnknown && (
                  <text
                    className="unknown"
                    transform={`translate(1, ${TEXT_ADJUST_Y})`}
                    style={{ fill: 'darkgray' }}
                    x={LABEL_MAX_WIDTH + (displayByEmissions ? co2Scale(0) : powerScale(0))}
                  >
                    ?
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
};

export default connect(mapStateToProps)(CountryTable);
