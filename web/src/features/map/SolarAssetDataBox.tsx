import GlassContainer from 'components/GlassContainer'; // Import GlassContainer
import { useAtomValue, useSetAtom } from 'jotai';
import { X } from 'lucide-react'; // Using Lucide X icon

import { selectedSolarAssetAtom } from './mapAtoms';

// Helper to format date string (YYYY-MM-DDTHH:mm:ssZ) to YYYY-MM-DD
const formatDate = (dateString: string | undefined | null) => {
  if (!dateString) {
    return 'N/A';
  }
  try {
    return new Date(dateString).toISOString().split('T')[0];
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

  if (!selectedAsset) {
    return null;
  }

  const { properties } = selectedAsset;

  const handleClose = () => {
    setSelectedAsset(null);
  };

  const name = properties.name || properties.ASSET_NAME || 'Unnamed Asset';
  const capacityMw = Number.parseFloat(String(properties.capacity_mw));
  const source = properties.source || 'N/A';
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
          <span>Source:</span>
          {source.startsWith('http://') || source.startsWith('https://') ? (
            <a
              href={source}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-blue-600 hover:underline dark:text-blue-400"
            >
              {source}
            </a>
          ) : (
            <span className="font-medium text-gray-800 dark:text-gray-200">{source}</span>
          )}
        </div>
        <div className="flex justify-between">
          <span>Capacity Data Updated:</span>
          <span className="font-medium text-gray-800 dark:text-gray-200">
            {capacityUpdateDate}
          </span>
        </div>
      </div>
    </GlassContainer>
  );
}
