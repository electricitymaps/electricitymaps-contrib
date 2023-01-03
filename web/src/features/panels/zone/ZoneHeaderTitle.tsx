import Badge from 'components/Badge';
import { CountryFlag } from 'components/Flag';
import { TimeDisplay } from 'components/TimeDisplay';
import { HiArrowLeft } from 'react-icons/hi2';
import { Link } from 'react-router-dom';
import { getCountryName, getZoneName, useTranslation } from 'translation/translation';
import { createToWithState } from 'utils/helpers';

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
  const { __ } = useTranslation();
  const title = getZoneName(zoneId);
  const isSubZone = zoneId.includes('-');
  const countryName = getCountryName(zoneId);
  const returnToMapLink = createToWithState('/map');

  return (
    <div className="flex flex-row pl-2">
      <Link
        className="text-3xl mr-4 self-center"
        to={returnToMapLink}
        data-test-id="left-panel-back-button"
      >
        <HiArrowLeft />
      </Link>
      <div>
        <div className="mb-0.5 flex items-center space-x-1.5 ">
          <CountryFlag
            zoneId={zoneId}
            size={18}
            className="mr-1 shadow-[0_0px_3px_rgba(0,0,0,0.2)]"
          />
          <div className="flex w-[320px] flex-row overflow-hidden">
            <h2 className="truncate font-medium" data-test-id="zone-name">
              {title}
            </h2>
            {isSubZone && (
              <p className="ml-2 flex w-auto items-center whitespace-nowrap rounded-full bg-gray-200 py-0.5 px-2  text-xs dark:bg-gray-900">
                {countryName || zoneId}
              </p>
            )}
          </div>
        </div>
        <div className="flex h-3 flex-wrap items-center gap-1 text-center">
          {isEstimated && (
            <Badge type="warning" key={'badge-est'}>
              {__('country-panel.estimated')}
            </Badge>
          )}
          {isAggregated && (
            <Badge key={'badge-agg'}>{__('country-panel.aggregated')}</Badge>
          )}
          <TimeDisplay className="whitespace-nowrap text-xs" />
        </div>
      </div>
    </div>
  );
}
