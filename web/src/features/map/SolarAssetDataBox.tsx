import GlassContainer from 'components/GlassContainer'; // Import GlassContainer
import { useAtomValue, useSetAtom } from 'jotai';
import { X } from 'lucide-react'; // Using Lucide X icon
import { useLocation } from 'react-router-dom';
import { TimeRange } from 'utils/constants';
import { useNavigateWithParameters } from 'utils/helpers';

import { selectedSolarAssetAtom } from './mapAtoms';

// Helper to format date string (YYYY-MM-DDTHH:mm:ssZ) to MonthName Day, Year
const formatDate = (dateString: string | undefined | null) => {
  if (!dateString) {
    return 'N/A';
  }
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return 'Invalid Date';
  }
};

// Helper to get a color based on status - can be expanded
const getStatusColor = (status: string | undefined) => {
  if (!status) {
    return 'bg-gray-400'; // Default grey for unknown for the circle
  } // Default
  switch (status.toLowerCase()) {
    case 'operating':
    case 'operational':
    case 'commissioned': {
      return 'bg-green-500'; // Green for operational
    }
    case 'planned': {
      return 'bg-blue-500'; // Blue for planned
    }
    case 'construction': {
      return 'bg-yellow-500'; // Yellow for construction
    }
    case 'cancelled':
    case 'retired': {
      return 'bg-red-500'; // Red for cancelled/retired
    }
    default: {
      return 'bg-gray-400'; // Default grey for any other status
    }
  }
};

export default function SolarAssetDataBox() {
  const selectedAsset = useAtomValue(selectedSolarAssetAtom);
  const setSelectedAsset = useSetAtom(selectedSolarAssetAtom);
  const navigate = useNavigateWithParameters();
  const location = useLocation();

  if (!selectedAsset) {
    return null;
  }

  const { properties } = selectedAsset;

  // Debug all properties to find potential URL fields
  console.log('[SolarAssetDataBox] All properties:', properties);
  const possibleUrlFields = Object.entries(properties).filter(
    ([key, value]) =>
      typeof value === 'string' &&
      (value.startsWith('http://') ||
        value.startsWith('https://') ||
        value.startsWith('www.'))
  );
  console.log('[SolarAssetDataBox] Possible URL fields:', possibleUrlFields);

  const handleClose = () => {
    setSelectedAsset(null);

    // Check if we're currently on a solar asset URL (identifiable by /zone/solar-asset-)
    const isSolarAssetPath = location.pathname.includes('/zone/solar-asset-');

    if (isSolarAssetPath) {
      // Extract the current time range and resolution from the path
      const pathParts = location.pathname.split('/');
      let timeRange = TimeRange.H72; // Default to 72h
      let resolution = 'hourly';

      // Correctly find the index of the solar-asset-ID part
      const solarAssetIdPathIndex = pathParts.findIndex((part) =>
        part.startsWith('solar-asset-')
      );

      if (solarAssetIdPathIndex !== -1 && pathParts.length > solarAssetIdPathIndex + 2) {
        // Time range is the part after solar-asset-ID, resolution is after time range
        const pathTimeRange = pathParts[solarAssetIdPathIndex + 1];
        const pathResolution = pathParts[solarAssetIdPathIndex + 2];

        if (
          pathTimeRange &&
          Object.values(TimeRange).includes(pathTimeRange as TimeRange)
        ) {
          timeRange = pathTimeRange as TimeRange;
        }
        if (pathResolution) {
          resolution = pathResolution;
        }
      }

      // Use the navigate function to change the URL to the map view
      // This ensures React Router is aware of the change for consistent state updates.
      navigate({
        to: '/map',
        timeRange,
        resolution,
        keepHashParameters: true, // This preserves existing query params like ?remote=true
      });
    }
  };

  const name = properties.name || properties.ASSET_NAME || 'Unnamed Asset';
  const capacityMw = Number.parseFloat(String(properties.capacity_mw));
  const source = properties.source || 'N/A';

  // Try to find a URL from various possible fields
  let sourceUrl = properties.source_url || properties.sourceUrl || properties.url || null;

  // If source itself is a URL, use it
  if (
    typeof source === 'string' &&
    (source.startsWith('http://') || source.startsWith('https://'))
  ) {
    sourceUrl = source;
  }

  // Handle URLs that start with www. but don't have a protocol
  if (typeof sourceUrl === 'string' && sourceUrl.startsWith('www.')) {
    sourceUrl = 'https://' + sourceUrl;
  }

  // For debugging - explicitly check if the URL is valid
  let isValidUrl = false;
  try {
    if (sourceUrl) {
      new URL(sourceUrl); // This will throw if the URL is invalid
      isValidUrl = true;
    }
  } catch (error) {
    console.error('[SolarAssetDataBox] Invalid URL:', sourceUrl, error);
  }

  console.log('[SolarAssetDataBox] Final sourceUrl:', sourceUrl, 'isValid:', isValidUrl);

  // Hardcoded fallback URL for now - remove this when real URLs are working
  if (!isValidUrl) {
    sourceUrl =
      'https://www.globalenergymonitor.org/projects/global-solar-power-tracker/';
    isValidUrl = true;
  }

  const commissionYear = properties.commission_year
    ? String(Math.floor(Number(properties.commission_year)))
    : null;
  const capacityUpdateDate = formatDate(String(properties.capacity_update_date));
  let status = properties.status ? String(properties.status) : 'Unknown';
  let isCommissionedInPast = false;

  if (commissionYear) {
    const numericCommissionYear = Number.parseInt(commissionYear, 10);
    const currentYear = new Date().getFullYear();
    if (!Number.isNaN(numericCommissionYear) && numericCommissionYear <= currentYear) {
      isCommissionedInPast = true;
      if (status.toLowerCase() === 'unknown') {
        status = 'Operational';
      }
    }
  }

  return (
    <GlassContainer className="pointer-events-auto absolute left-3 top-3 z-[21] flex flex-col p-4 shadow-lg">
      {/* Energy Type Tag - with icon */}
      <div className="mb-2 flex items-center justify-between">
        <span
          className={`inline-flex items-center rounded-full bg-yellow-500 px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider text-white`}
        >
          <img src="/images/solar_asset.png" alt="Solar" className="mr-1.5 h-3.5 w-3.5" />
          Solar
        </span>
      </div>

      {/* Header with Name and Close Button - icon removed from here */}
      <div className="mb-1 flex items-start justify-between">
        <div className="flex items-center">
          <h2 className="pr-2 text-xl font-bold text-gray-800 dark:text-gray-100">
            {name}
          </h2>
        </div>
        <button
          onClick={handleClose}
          className="flex-shrink-0 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          aria-label="Close"
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      {/* Details Section */}
      <div className="space-y-2 pt-3 text-xs text-gray-600 dark:border-gray-700 dark:text-gray-400">
        {/* Divider and Larger Font for Capacity */}
        <div className="border-t border-gray-200 dark:border-gray-700" />
        {!Number.isNaN(capacityMw) && (
          <div className="flex justify-between text-sm">
            <span className="font-bold">Capacity:</span>
            <span className="font-bold text-gray-800 dark:text-gray-200">
              {`${capacityMw.toFixed(1)} MW`}
            </span>
          </div>
        )}
        <div className="flex items-center justify-between">
          <span>Status:</span>
          {/* Status with colored circle */}
          <div className="flex items-center">
            <span
              className={`mr-1.5 h-2.5 w-2.5 rounded-full ${getStatusColor(status)}`}
              aria-hidden="true"
            />
            <span className="font-medium text-gray-800 dark:text-gray-200">{status}</span>
          </div>
        </div>
        {commissionYear && (
          <div className="flex justify-between">
            <span>
              {isCommissionedInPast ? 'Operational since:' : 'Commission Year:'}
            </span>
            <span className="font-medium text-gray-800 dark:text-gray-200">
              {commissionYear}
            </span>
          </div>
        )}
        <div className="flex justify-between">
          <span>Capacity Data Updated:</span>
          <span className="font-medium text-gray-800 dark:text-gray-200">
            {capacityUpdateDate}
          </span>
        </div>

        {/* Divider */}
        <div className="my-2 border-t border-gray-200 dark:border-gray-700" />

        <div className="flex flex-row">
          <span className="mr-1 font-medium">Source:</span>
          <span className="font-medium text-gray-800 dark:text-gray-200">
            Global Solar Power Tracker, Global Energy Monitor and TransitionZero, February
            2025 release.
            {isValidUrl && sourceUrl ? (
              <>
                <br />
                <a
                  href={sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  Global Energy Monitor Wiki page.
                </a>
              </>
            ) : null}
          </span>
        </div>
      </div>
    </GlassContainer>
  );
}
