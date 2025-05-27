import { CountryFlag } from 'components/Flag';
import InternalLink from 'components/InternalLink';
import { BatteryCharging } from 'lucide-react';

import { SearchResultType, SolarAssetRowType } from './getSearchData';
import { ZoneRowType } from './ZoneList';

interface SearchResultRowProps {
  result: SearchResultType;
  isSelected: boolean;
}

// Type guard to check if a result is a ZoneRowType
function isZoneResult(result: SearchResultType): result is ZoneRowType {
  return (result as ZoneRowType).zoneId !== undefined;
}

// Type guard to check if a result is a SolarAssetRowType
function isSolarAssetResult(result: SearchResultType): result is SolarAssetRowType {
  return (result as SolarAssetRowType).type === 'solar';
}

export default function SearchResultRow({ result, isSelected }: SearchResultRowProps) {
  // Base classes for all result rows
  const baseClasses = `group flex h-11 w-full items-center gap-2 p-4 hover:bg-neutral-200/50 focus:outline-0 focus-visible:border-l-4 focus-visible:border-brand-green focus-visible:bg-brand-green/10 focus-visible:outline-0 dark:hover:bg-neutral-700/50 dark:focus-visible:bg-brand-green/10 ${
    isSelected ? 'bg-neutral-200/50 dark:bg-neutral-700/50' : ''
  }`;

  if (isZoneResult(result)) {
    // Render zone result row
    return (
      <InternalLink
        className={baseClasses}
        key={result.zoneId}
        to={`/zone/${result.zoneId}`}
        data-testid="zone-list-link"
      >
        <CountryFlag
          zoneId={result.zoneId}
          size={18}
          className="shadow-[0_0px_3px_rgba(0,0,0,0.2)]"
        />

        <div className="flex min-w-0 grow flex-row items-center justify-between">
          <h3 className="min-w-0 truncate">{result.zoneName}</h3>
          {result.countryName && (
            <span className="ml-2 shrink-0 truncate text-xs font-normal text-neutral-400 dark:text-neutral-400">
              {result.countryName}
            </span>
          )}
        </div>
      </InternalLink>
    );
  } else if (isSolarAssetResult(result)) {
    // Encode the asset ID for URL safety
    const encodedAssetId = encodeURIComponent(result.id);

    // Get the base URL from the current location
    const baseUrl = window.location.origin;

    // Create a link using the zone path pattern but with our special identifier
    // This will look like: /zone/solar-asset-[encodedName]/72h/hourly?remote=true
    const assetLink = `${baseUrl}/zone/solar-asset-${encodedAssetId}/72h/hourly?remote=true`;

    // Render solar asset result row with regular anchor tag that navigates in the current tab
    return (
      <a
        className={baseClasses}
        key={result.id}
        href={assetLink}
        data-testid="solar-asset-list-link"
      >
        <div className="flex h-[18px] w-[18px] items-center justify-center">
          <BatteryCharging size={16} className="text-yellow-500" />
        </div>

        <div className="flex min-w-0 grow flex-row items-center justify-between">
          <h3 className="min-w-0 truncate">{result.name}</h3>
          <div className="ml-2 flex shrink-0 flex-col items-end">
            {result.country && (
              <span className="truncate text-xs font-normal text-neutral-400 dark:text-neutral-400">
                {result.country}
              </span>
            )}
            {result.capacity && (
              <span className="truncate text-xs font-normal text-neutral-400 dark:text-neutral-400">
                {result.capacity}
              </span>
            )}
          </div>
        </div>
      </a>
    );
  }

  // Fallback for any other result type (shouldn't happen)
  return null;
}
