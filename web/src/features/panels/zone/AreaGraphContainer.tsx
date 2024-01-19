import BreakdownChart from 'features/charts/BreakdownChart';
import CarbonChart from 'features/charts/CarbonChart';
import EmissionChart from 'features/charts/EmissionChart';
import NetExchangeChart from 'features/charts/NetExchangeChart';
import PriceChart from 'features/charts/PriceChart';
import { TimeAverages } from 'utils/constants';

import Divider from './Divider';

export default function AreaGraphContainer({
  datetimes,
  timeAverage,
  displayByEmissions,
  hasEstimationPill,
}: {
  datetimes: Date[];
  timeAverage: TimeAverages;
  displayByEmissions: boolean;
  hasEstimationPill: boolean;
}) {
  return (
    <div>
      {displayByEmissions ? (
        <EmissionChart
          datetimes={datetimes}
          timeAverage={timeAverage}
          hasEstimationPill={hasEstimationPill}
        />
      ) : (
        <CarbonChart
          datetimes={datetimes}
          timeAverage={timeAverage}
          hasEstimationPill={hasEstimationPill}
        />
      )}
      <BreakdownChart
        displayByEmissions={displayByEmissions}
        datetimes={datetimes}
        timeAverage={timeAverage}
        hasEstimationPill={hasEstimationPill}
      />
      <NetExchangeChart datetimes={datetimes} timeAverage={timeAverage} />
      <PriceChart datetimes={datetimes} timeAverage={timeAverage} />
      <Divider />
    </div>
  );
}
