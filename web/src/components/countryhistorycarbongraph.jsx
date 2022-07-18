import React, { useMemo, useState } from 'react';
import { connect } from 'react-redux';

import { getTooltipPosition } from '../helpers/graph';
import { useCo2ColorScale } from '../hooks/theme';
import { useCurrentZoneHistory } from '../hooks/redux';

import MapCountryTooltip from './tooltips/mapcountrytooltip';
import AreaGraph from './graph/areagraph';
import { getCO2IntensityByMode } from '../helpers/zonedata';

const prepareGraphData = (historyData, co2ColorScale, electricityMixMode) => {
  if (!historyData || !historyData[0] || !historyData[0].hasData) {
    // Incomplete data
    return {};
  }

  const data = historyData.map((d) => ({
    carbonIntensity: getCO2IntensityByMode(d, electricityMixMode),
    datetime: new Date(d.stateDatetime),
    // Keep a pointer to original data
    meta: d,
  }));
  const layerKeys = ['carbonIntensity'];
  const layerFill = (key) => (d) => co2ColorScale(d.data[key]);
  return { data, layerKeys, layerFill };
};

const mapStateToProps = (state) => ({
  electricityMixMode: state.application.electricityMixMode,
  isMobile: state.application.isMobile,
});

const CountryHistoryCarbonGraph = ({ electricityMixMode, isMobile }) => {
  const [tooltip, setTooltip] = useState(null);
  const co2ColorScale = useCo2ColorScale();

  const historyData = useCurrentZoneHistory();

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill } = useMemo(
    () => prepareGraphData(historyData, co2ColorScale, electricityMixMode),
    [historyData, co2ColorScale, electricityMixMode]
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
        testId="history-carbon-graph"
        data={data}
        layerKeys={layerKeys}
        layerFill={layerFill}
        valueAxisLabel="g / kWh"
        markerUpdateHandler={markerUpdateHandler}
        markerHideHandler={markerHideHandler}
        isMobile={isMobile}
        height="8em"
      />
      {tooltip && (
        <MapCountryTooltip
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

export default connect(mapStateToProps)(CountryHistoryCarbonGraph);
