import useGetZone from 'api/getZone';
import BreakdownChart from 'features/charts/BreakdownChart';
import CarbonChart from 'features/charts/CarbonChart';
import PriceChart from 'features/charts/PriceChart';
import { useAtom } from 'jotai';
import { Navigate, useParams } from 'react-router-dom';
import { TimeAverages } from 'utils/constants';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state';
import { ZoneHeader } from './ZoneHeader';

export default function ZoneDetails(): JSX.Element {
  const { zoneId } = useParams();
  const [timeAverage] = useAtom(timeAverageAtom);
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
    return <div>none</div>;
  }

  const datetimes = Object.keys(data.zoneStates).map((key) => new Date(key));

  // TODO: Consider if we should move the items relying on this data to its own component instead
  // TODO: Fix rendering issue where this is shortly unavailable for some reason
  const selectedData = data[0].zoneStates[selectedDatetime];
  if (!selectedData) {
    return <div></div>;
  }
  const { estimationMethod, co2intensity, fossilFuelRatio, renewableRatio } =
    selectedData;
  const lowCarbonRatio = 1 - fossilFuelRatio; // TODO: Handle null values
  const isAggregated = timeAverage !== TimeAverages.HOURLY;
  const isEstimated = Boolean(estimationMethod);

  return (
    <div>
      <ZoneHeader
        zoneId={zoneId}
        isEstimated={isEstimated}
        isAggregated={isAggregated}
        co2intensity={co2intensity}
        lowCarbonRatio={lowCarbonRatio}
        renewableRatio={renewableRatio}
      />
      <CarbonChart datetimes={datetimes} timeAverage={timeAverage} />
      <BreakdownChart timeAverage={timeAverage} datetimes={datetimes} />
      <PriceChart datetimes={datetimes} timeAverage={timeAverage} />
    </div>
  );
}
