import Badge from 'components/Badge';
import { CountryFlag } from 'components/Flag';
import { TimeDisplay } from 'components/TimeDisplay';
import TooltipWrapper from 'components/tooltips/TooltipWrapper';
import { HiArrowLeft } from 'react-icons/hi2';
import { Link } from 'react-router-dom';
import { getCountryName, getZoneName, useTranslation } from 'translation/translation';
import { createToWithState } from 'utils/helpers';
import { getDisclaimer } from './util';

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
  const returnToMapLink = createToWithState('/map');
  const countryName = getCountryName(zoneId);
  const disclaimer = getDisclaimer(zoneId);

  return (
    <div className="flex w-full grow flex-row overflow-hidden pb-2 pl-2">
      <Link
        className="text-3xl self-center py-4 pr-4"
        to={returnToMapLink}
        data-test-id="left-panel-back-button"
      >
        <HiArrowLeft />
      </Link>

      <div className="w-full overflow-hidden">
        <div className="flex w-full  flex-row justify-between">
          <div className="mb-0.5 flex  w-full  justify-between">
            <div className="flex w-full flex-row items-center pr-4 sm:pr-0 ">
              <CountryFlag
                zoneId={zoneId}
                size={18}
                className="shadow-[0_0px_3px_rgba(0,0,0,0.2)]"
              />
              <TooltipWrapper
                tooltipContent={title.length > 20 ? title : undefined}
                side="bottom"
              >
                <div className="ml-2 flex w-full flex-row overflow-hidden">
                  <h2 className="truncate text-lg font-medium" data-test-id="zone-name">
                    {title}
                  </h2>
                  {isSubZone && (
                    <div className="ml-2 flex w-auto items-center rounded-full bg-gray-200 px-2 py-0.5  text-sm dark:bg-gray-800/80">
                      <p className="w-full truncate">{countryName || zoneId}</p>
                    </div>
                  )}
                </div>
              </TooltipWrapper>
              {disclaimer && (
                <TooltipWrapper side="bottom" tooltipContent={disclaimer}>
                  <div className="ml-2 mr-4 h-6 w-6 shrink-0 select-none rounded-full bg-white text-center drop-shadow dark:border dark:border-gray-500 dark:bg-gray-900">
                    <p>i</p>
                  </div>
                </TooltipWrapper>
              )}
            </div>
          </div>
        </div>
        <div className="flex h-auto flex-wrap items-center gap-1 text-center">
          {isEstimated && (
            <Badge type="warning" key={'badge-est'}>
              {__('country-panel.estimated')}
            </Badge>
          )}
          {isAggregated && (
            <Badge key={'badge-agg'}>{__('country-panel.aggregated')}</Badge>
          )}
          <TimeDisplay className="whitespace-nowrap text-sm" />
        </div>
      </div>
    </div>
  );
}
