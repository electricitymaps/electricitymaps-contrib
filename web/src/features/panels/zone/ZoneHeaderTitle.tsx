import Badge from 'components/Badge';
import { CountryFlag } from 'components/Flag';
import { TimeDisplay } from 'components/TimeDisplay';
import { HiArrowLeft } from 'react-icons/hi2';
import { Link } from 'react-router-dom';
import { getZoneName } from 'translation/translation';
import { CountryTag } from './CountryTag';

interface ZoneHeaderTitleProps {
  zoneId: string;
  isEstimated?: boolean;
  isAggregated?: boolean;
}

export default function ZoneHeaderTitle({
  zoneId,
  isAggregated,
  isEstimated,
}: ZoneHeaderTitleProps) {
  const title = getZoneName(zoneId);
  const isSubZone = zoneId.includes('-');

  return (
    <div className="flex flex-row pl-2">
      <Link className="text-3xl mr-4 self-center " to="/">
        <HiArrowLeft />
      </Link>
      <div>
        <div className="mb-0.5 flex items-center space-x-1.5 ">
          <CountryFlag
            zoneId={zoneId}
            size={18}
            className="mr-1 shadow-[0_0px_3px_rgba(0,0,0,0.2)]"
          />
          <h2 className="font-medium">
            {title}
            <span className="absolute ml-1 -mt-0.5">
              {isSubZone && <CountryTag zoneId={zoneId} />}
            </span>
          </h2>
        </div>
        <div className="flex flex-wrap items-center gap-1 text-center">
          {isEstimated && (
            <Badge type="warning" key={'badge-est'}>
              Estimated
            </Badge>
          )}
          {isAggregated && <Badge key={'badge-agg'}>Aggregated</Badge>}
          <TimeDisplay className="whitespace-nowrap text-xs" />
        </div>
      </div>
    </div>
  );
}
