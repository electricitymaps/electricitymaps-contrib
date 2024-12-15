import { HorizontalDivider } from 'components/Divider';
import CarbonChart from 'features/charts/CarbonChart';
import EmissionChart from 'features/charts/EmissionChart';
import NetExchangeChart from 'features/charts/NetExchangeChart';
import OriginChart from 'features/charts/OriginChart';
import PriceChart from 'features/charts/PriceChart';
import { TimeRange } from 'utils/constants';

export default function AreaGraphContainer({
  datetimes,
  timeRange,
  displayByEmissions,
}: {
  datetimes: Date[];
  timeRange: TimeRange;
  displayByEmissions: boolean;
}) {
  return (
    <div className="flex flex-col gap-1">
      {displayByEmissions ? (
        <EmissionChart datetimes={datetimes} timeRange={timeRange} />
      ) : (
        <CarbonChart datetimes={datetimes} timeRange={timeRange} />
      )}
      <OriginChart
        displayByEmissions={displayByEmissions}
        datetimes={datetimes}
        timeRange={timeRange}
      />
      <NetExchangeChart datetimes={datetimes} timeRange={timeRange} />
      <PriceChart datetimes={datetimes} timeRange={timeRange} />
      <HorizontalDivider />
    </div>
  );
}
