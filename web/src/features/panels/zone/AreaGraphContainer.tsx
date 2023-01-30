import BreakdownChart from 'features/charts/BreakdownChart';
import CarbonChart from 'features/charts/CarbonChart';
import EmissionChart from 'features/charts/EmissionChart';
import PriceChart from 'features/charts/PriceChart';
import { TimeAverages } from 'utils/constants';
import Divider from './Divider';

export default function AreaGraphContainer({
  datetimes,
  timeAverage,
  displayByEmissions,
}: {
  datetimes: Date[];
  timeAverage: TimeAverages;
  displayByEmissions: boolean;
}) {
  return (
    <div>
      {displayByEmissions ? (
        <EmissionChart datetimes={datetimes} timeAverage={timeAverage} />
      ) : (
        <CarbonChart datetimes={datetimes} timeAverage={timeAverage} />
      )}
      <BreakdownChart
        displayByEmissions={displayByEmissions}
        datetimes={datetimes}
        timeAverage={timeAverage}
      />
      <PriceChart datetimes={datetimes} timeAverage={timeAverage} />
      <Divider />
    </div>
  );
}
