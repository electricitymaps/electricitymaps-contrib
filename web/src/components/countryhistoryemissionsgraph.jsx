import React, { useMemo, useState } from 'react';
import { connect } from 'react-redux';
import { scaleLinear } from 'd3-scale';
import { max as d3Max } from 'd3-array';

import { getTooltipPosition } from '../helpers/graph';
import { useCurrentZoneHistory } from '../hooks/redux';
import { tonsPerHourToGramsPerMinute } from '../helpers/math';
import { getTotalElectricity } from '../helpers/zonedata';

import CountryPanelEmissionsTooltip from './tooltips/countrypanelemissionstooltip';
import AreaGraph from './graph/areagraph';

const prepareGraphData = (historyData) => {
  if (!historyData || !historyData[0]) {
    return {};
  }

  const data = historyData.map((d) => ({
    emissions: tonsPerHourToGramsPerMinute(getTotalElectricity(d, true)),
    datetime: new Date(d.stateDatetime),
    // Keep a pointer to original data
    meta: d,
  }));

  const maxEmissions = d3Max(data.map((d) => d.emissions));
  const emissionsColorScale = scaleLinear().domain([0, maxEmissions]).range(['yellow', 'brown']);

  const layerKeys = ['emissions'];
  const layerFill = (key) => (d) => emissionsColorScale(d.data[key]);
  return { data, layerKeys, layerFill };
};

const mapStateToProps = (state) => ({
  isMobile: state.application.isMobile,
});

const CountryHistoryEmissionsGraph = ({ isMobile }) => {
  const [tooltip, setTooltip] = useState(null);

  const historyData = useCurrentZoneHistory();

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill } = useMemo(() => prepareGraphData(historyData), [historyData]);

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
        testId="history-emissions-graph"
        data={data}
        layerKeys={layerKeys}
        layerFill={layerFill}
        valueAxisLabel="tCO₂eq / min"
        markerUpdateHandler={markerUpdateHandler}
        markerHideHandler={markerHideHandler}
        isMobile={isMobile}
        height="8em"
      />
      {tooltip && (
        <CountryPanelEmissionsTooltip
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

export default connect(mapStateToProps)(CountryHistoryEmissionsGraph);
