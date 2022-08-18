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

const prepareGraphData = (historyData: any) => {
  if (!historyData || !historyData[0]) {
    return {};
  }

  const data = historyData.map((d: any) => ({
    emissions: tonsPerHourToGramsPerMinute(getTotalElectricity(d, true)),
    datetime: new Date(d.stateDatetime),

    // Keep a pointer to original data
    meta: d,
  }));

  const maxEmissions = d3Max(data.map((d: any) => d.emissions));
  const emissionsColorScale = scaleLinear().domain([0, maxEmissions]).range(['yellow', 'brown']);

  const layerKeys = ['emissions'];
  const layerFill = (key: any) => (d: any) => emissionsColorScale(d.data[key]);
  return { data, layerKeys, layerFill };
};

const mapStateToProps = (state: any) => ({
  isMobile: state.application.isMobile,
});

const CountryHistoryEmissionsGraph = ({ isMobile }: any) => {
  const [tooltip, setTooltip] = useState(null);

  const historyData = useCurrentZoneHistory();

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill } = useMemo(() => prepareGraphData(historyData), [historyData]);

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
        // @ts-expect-error TS(2322): Type '{ testId: string; data: any; layerKeys: stri... Remove this comment to see the full error message
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

export default connect(mapStateToProps)(CountryHistoryEmissionsGraph);
