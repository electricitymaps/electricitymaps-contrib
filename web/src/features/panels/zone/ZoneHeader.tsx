import Badge from 'components/Badge';
import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import { CountryTag } from './CountryTag';
import ZoneHeaderTitle from './ZoneHeaderTitle';

interface ZoneHeaderProps {
  zoneId: string;
  date: string;
  isEstimated?: boolean;
  isAggregated?: boolean;
}

export function ZoneHeader({ date, zoneId, isEstimated, isAggregated }: ZoneHeaderProps) {
  return (
    <div className="mt-1 grid w-full gap-y-5 sm:pr-4">
      <ZoneHeaderTitle
        title="Western Area Power Administration Rocky Mountain Region"
        formattedDate={date}
        labels={[
          isEstimated && (
            <Badge type="warning" key={'badge-est'}>
              Estimated
            </Badge>
          ),
          isAggregated && <Badge key={'badge-agg'}>Aggregated</Badge>,
        ]}
        countryTag={<CountryTag zoneId={'US-MISO'} />}
      />
      <div className="flex flex-row justify-evenly">
        <CarbonIntensitySquare co2intensity={60} withSubtext />
        <CircularGauge name="Low-carbon" percentage={78} />
        <CircularGauge name="Renewable" percentage={65} />
      </div>
    </div>
  );
}
