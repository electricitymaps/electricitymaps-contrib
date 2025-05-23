import { useAtomValue, useSetAtom } from 'jotai';
import { ArrowLeft } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { useNavigateWithParameters } from 'utils/helpers';

import GenericPanel from '../../components/panel/GenericPanel';
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

  console.log('random');
  const { properties } = selectedAsset;

  // Debug all properties to find potential URL fields
  console.log('[SolarAssetDataBox] All properties:', properties);
  const possibleUrlFields = Object.entries(properties).filter(
    ([_, value]) =>
      typeof value === 'string' &&
      (value.startsWith('http://') ||
        value.startsWith('https://') ||
        value.startsWith('www.'))
  );
  console.log('[SolarAssetDataBox] Possible URL fields:', possibleUrlFields);

  const handleClose = () => {
    setSelectedAsset(null);
    // Check if we are on a path that implies an asset is selected in the URL structure.
    // This logic might need adjustment depending on final routing for assets.
    const isAssetPath =
      location.pathname.includes('/solar-asset/') ||
      location.pathname.includes('/zone/solar-asset-');

    if (isAssetPath) {
      // Navigate to the base map view, preserving current map parameters if possible
      // This part is a simplified navigation, assuming we want to go back to /map
      // and that navigate hook handles existing params like timeRange, resolution.
      navigate({ to: '/map', keepHashParameters: true });
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

  const backButton = (
    <button
      onClick={handleClose}
      className="self-center p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
      aria-label="Back to map"
      data-testid="solar-asset-data-box-back-button"
    >
      <ArrowLeft className="h-5 w-5" />
    </button>
  );

  return (
    <GenericPanel
      title={name}
      iconSrc="/images/solar_asset.png"
      customHeaderStartContent={backButton}
      contentClassName="p-3 md:p-4"
    >
      {/* Content for the solar asset details */}
      <div className="space-y-3 text-sm text-gray-700 dark:text-gray-300">
        {!Number.isNaN(capacityMw) && (
          <div className="flex justify-between font-medium">
            <span>Capacity:</span>
            <span className="text-gray-900 dark:text-gray-100">
              {`${capacityMw.toFixed(1)} MW`}
            </span>
          </div>
        )}
        <div className="flex items-center justify-between">
          <span>Status:</span>
          <div className="flex items-center">
            <span
              className={`mr-1.5 h-2.5 w-2.5 rounded-full ${getStatusColor(status)}`}
              aria-hidden="true"
            />
            <span className="font-medium text-gray-900 dark:text-gray-100">{status}</span>
          </div>
        </div>
        {commissionYear && (
          <div className="flex justify-between">
            <span>
              {isCommissionedInPast ? 'Operational since:' : 'Commission Year:'}
            </span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {commissionYear}
            </span>
          </div>
        )}
        {capacityUpdateDate && capacityUpdateDate !== 'N/A' && (
          <div className="flex justify-between">
            <span>Capacity Data Updated:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {capacityUpdateDate}
            </span>
          </div>
        )}

        <div className="border-t border-gray-200 pt-2 dark:border-gray-700" />

        <div>
          <span className="mr-1 font-semibold">Source:</span>
          <span className="text-gray-900 dark:text-gray-100">
            Global Solar Power Tracker, Global Energy Monitor and TransitionZero, February
            2025 release.
            {isValidUrl && sourceUrl && (
              <>
                <br />
                <a
                  href={sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  Learn more at Global Energy Monitor.
                </a>
              </>
            )}
          </span>
        </div>
      </div>
    </GenericPanel>
  );
}
