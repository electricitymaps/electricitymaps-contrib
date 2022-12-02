import useGetZone from 'api/getZone';
import BreakdownChart from 'features/charts/BreakdownChart';
import CarbonChart from 'features/charts/CarbonChart';
import EmissionChart from 'features/charts/EmissionChart';
import PriceChart from 'features/charts/PriceChart';
import { useAtom } from 'jotai';
import { Navigate, useParams } from 'react-router-dom';
import { TimeAverages } from 'utils/constants';
import {
  displayByEmissionsAtom,
  selectedDatetimeIndexAtom,
  timeAverageAtom,
} from 'utils/state/atoms';
import DisplayByEmissionToggle from './DisplayByEmissionToggle';
import { ZoneHeader } from './ZoneHeader';

export default function ZoneDetails(): JSX.Element {
  const { zoneId } = useParams();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const { data } = useGetZone({
    enabled: Boolean(zoneId),
  });

  if (!zoneId) {
    return <Navigate to="/" replace />;
  }

  // TODO: Handle error state
  // TODO: Handle loading state nicely (let's keep country name in the header)
  // TODO: Show zone title while data is loading

  if (!data) {
    return <div>No data</div>;
  }

  const datetimes = Object.keys(data.zoneStates).map((key) => new Date(key));

  // TODO: Consider if we should move the items relying on this data to its own component instead
  // TODO: Fix rendering issue where this is shortly unavailable for some reason
  const selectedData = data.zoneStates[selectedDatetime.datetimeString];
  if (!selectedData) {
    return <div></div>;
  }
  const { estimationMethod, co2intensity, fossilFuelRatio, renewableRatio } =
    selectedData;
  const lowCarbonRatio = 1 - fossilFuelRatio; // TODO: Handle null values
  const isAggregated = timeAverage !== TimeAverages.HOURLY;
  const isEstimated = Boolean(estimationMethod);

  return (
    <div
      className="mb-60" // Adding room to scroll past the time controller
    >
      <ZoneHeader
        zoneId={zoneId}
        isEstimated={isEstimated}
        isAggregated={isAggregated}
        co2intensity={co2intensity}
        lowCarbonRatio={lowCarbonRatio}
        renewableRatio={renewableRatio}
      />
      <DisplayByEmissionToggle />
      {displayByEmissions ? (
        <EmissionChart datetimes={datetimes} timeAverage={timeAverage} />
      ) : (
        <CarbonChart datetimes={datetimes} timeAverage={timeAverage} />
      )}
      <BreakdownChart datetimes={datetimes} timeAverage={timeAverage} />
      <PriceChart datetimes={datetimes} timeAverage={timeAverage} />
    </div>
  );
}
