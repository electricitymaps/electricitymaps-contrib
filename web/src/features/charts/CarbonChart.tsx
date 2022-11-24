import { useCo2ColorScale } from 'hooks/theme';
import { useMemo } from 'react';
import { getCO2IntensityByMode } from 'utils/helpers';
import AreaGraph from './elements/AreaGraph';
import { noop } from './graphUtils';

const prepareGraphData = (
  historyData: any,
  co2ColorScale: any,
  electricityMixMode: any
) => {
  if (!historyData || !historyData[0] || historyData.every((d: any) => !d.isValid)) {
    // Incomplete data
    return {};
  }

  const data = historyData.map((d: any) => ({
    carbonIntensity: getCO2IntensityByMode(d, electricityMixMode),
    datetime: new Date(d.stateDatetime),
    // Keep a pointer to original data
    meta: d,
  }));
  const layerKeys = ['carbonIntensity'];
  const layerFill = (key: any) => (d: any) => co2ColorScale(d.data[key]);
  return { data, layerKeys, layerFill };
};

function CarbonChart({
  electricityMixMode,
  isMobile,
  historyData,
  datetimes,
  timeAverage,
}: any) {
  // const [tooltip, setTooltip] = useState(null);
  const co2ColorScale = useCo2ColorScale();

  // Recalculate graph data only when the history data is changed
  const { data, layerKeys, layerFill } = useMemo(
    () => prepareGraphData(historyData, co2ColorScale, electricityMixMode),
    [historyData, co2ColorScale, electricityMixMode]
  );

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
        testId="history-carbon-graph"
        data={data}
        layerKeys={layerKeys}
        layerFill={layerFill}
        valueAxisLabel="g / kWh"
        markerUpdateHandler={noop}
        markerHideHandler={noop}
        isMobile={false}
        isOverlayEnabled={false}
        height="8em"
        datetimes={datetimes}
        selectedTimeAggregate={timeAverage}
        selectedZoneTimeIndex={0}
      />
      {/* {tooltip && (
        <MapCountryTooltip
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

export default CarbonChart;
