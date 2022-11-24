import useGetZone from 'api/getZone';
import { data } from 'cypress/types/jquery';
import BreakdownChart from 'features/charts/BreakdownChart';
import CarbonChart from 'features/charts/CarbonChart';
import PriceChart from 'features/charts/PriceChart';
import { useAtom } from 'jotai';
import { Navigate, useParams } from 'react-router-dom';
import { timeAverageAtom } from 'utils/state';
import { ZoneHeader } from './ZoneHeader';

export default function ZoneDetails(): JSX.Element {
  const { zoneId } = useParams();
  const [timeAverage] = useAtom(timeAverageAtom);
  const { error, data, status } = useGetZone(timeAverage, zoneId, {
    enabled: Boolean(zoneId),
  });

  if (!zoneId) {
    return <Navigate to="/" replace />;
  }

  // TODO: Handle error state
  // TODO: Handle loading state nicely (let's keep country name in the header)

  if (!data) {
    return <div>none</div>;
  }
  const breakdownData = Object.values(data.zoneStates);
  const exchangeKeys: any[] = []; // TODO: Get exchange keys from data

  const datetimes = Object.keys(data.zoneStates).map((key) => new Date(key));

  return (
    <div>
      <ZoneHeader
        zoneId={zoneId}
        date="November 9, 2022 at 8:00"
        isEstimated
        isAggregated
      />
      <CarbonChart
        electricityMixMode="production"
        displayByEmissions={false}
        isMobile={false}
        isOverlayEnabled={false}
        historyData={breakdownData}
        exchangeKeys={exchangeKeys}
        datetimes={datetimes}
        timeAverage={timeAverage}
      />
      <BreakdownChart
        displayByEmissions={false}
        electricityMixMode="production"
        isMobile={false}
        isOverlayEnabled={false}
        historyData={breakdownData}
        exchangeKeys={exchangeKeys}
        timeAverage={timeAverage}
        datetimes={datetimes}
      />
      <PriceChart
        electricityMixMode="production"
        displayByEmissions={false}
        isMobile={false}
        isOverlayEnabled={false}
        historyData={breakdownData}
        exchangeKeys={exchangeKeys}
        datetimes={datetimes}
        timeAverage={timeAverage}
      />
    </div>
  );
}
