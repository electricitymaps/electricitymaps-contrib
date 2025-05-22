import GlassContainer from 'components/GlassContainer'; // Import GlassContainer
import { useAtomValue, useSetAtom } from 'jotai';
// import { XMarkIcon } from '@heroicons/react/24/solid'; // For the close button
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
    return 'bg-gray-400';
  } // Default
  switch (status.toLowerCase()) {
    case 'operating': {
      return 'bg-green-500';
    }
    case 'construction':
    case 'planned': {
      return 'bg-yellow-500';
    }
    case 'cancelled':
    case 'retired': {
      return 'bg-red-500';
    }
    default: {
      return 'bg-gray-400';
    }
  }
};

export default function SolarAssetDataBox() {
  const selectedAsset = useAtomValue(selectedSolarAssetAtom);
  const setSelectedAsset = useSetAtom(selectedSolarAssetAtom); // For the close button

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
  let status = properties.status ? String(properties.status) : 'Unknown'; // Get status

  // Infer status if commission year is in the past and status is Unknown
  if (commissionYear) {
    const numericCommissionYear = Number.parseInt(commissionYear, 10);
    const currentYear = new Date().getFullYear();
    if (
      !Number.isNaN(numericCommissionYear) &&
      numericCommissionYear <= currentYear &&
      status.toLowerCase() === 'unknown'
    ) {
      status = 'Operating';
    }
  }

  const MIN_SCALE_MW = 0; // Changed from 20 to 0
  const MAX_SCALE_MW = 200;
  let capacityPercentage = 0;
  if (!Number.isNaN(capacityMw)) {
    // Ensure capacityPercentage is calculated correctly even if capacityMw is outside the scale
    const normalizedCapacity = Math.max(0, capacityMw);
    capacityPercentage = Math.min(100, (normalizedCapacity / MAX_SCALE_MW) * 100);
    if (capacityMw < MIN_SCALE_MW) {
      capacityPercentage = 0;
    } // explicitly set to 0 if below min (though min is 0 now)
  }

  return (
    <GlassContainer className="pointer-events-auto absolute right-5 top-5 z-[999] flex w-96 flex-col p-4 shadow-lg">
      {/* Header with Name, Icon and Close Button */}
      <div className="mb-1 flex items-start justify-between">
        <div className="flex items-center">
          <img
            src="/images/solar_asset.png"
            alt="Solar Asset"
            className="mr-2 h-6 w-6" // Adjust size as needed
          />
          <h2 className="pr-2 text-xl font-bold text-gray-800 dark:text-gray-100">
            {name}
          </h2>
        </div>
        <button
          onClick={handleClose}
          className="flex-shrink-0 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          aria-label="Close"
        >
          {/* <XMarkIcon className="h-6 w-6" /> */}
          <X className="h-6 w-6" /> {/* Using Lucide X icon */}
        </button>
      </div>

      {/* Status Badge */}
      <div className="mb-3">
        <span
          className={`inline-block rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider text-white ${getStatusColor(
            status
          )}`}
        >
          {status}
        </span>
      </div>

      {/* Capacity Section */}
      <div className="mb-4">
        <div className="mb-1 flex justify-between text-sm text-gray-700 dark:text-gray-300">
          <span>Capacity</span>
          <span className="font-semibold text-gray-900 dark:text-gray-100">
            {Number.isNaN(capacityMw) ? 'N/A' : `${capacityMw.toFixed(1)} MW`}
          </span>
        </div>
        <div className="h-2.5 w-full rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            className="h-2.5 rounded-full bg-green-500" // Bar color remains green for capacity
            style={{ width: `${Number.isNaN(capacityMw) ? 0 : capacityPercentage}%` }}
          />
        </div>
        <div className="mt-1 flex justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>{MIN_SCALE_MW} MW</span>
          <span>{MAX_SCALE_MW} MW</span>
        </div>
      </div>

      {/* Details Section */}
      <div className="space-y-1 border-t border-gray-200 pt-3 text-xs text-gray-600 dark:border-gray-700 dark:text-gray-400">
        {commissionYear && (
          <div className="flex justify-between">
            <span>Commission Year:</span>
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
        <div className="flex justify-between">
          <span>Source:</span>
          <span className="font-medium text-gray-800 dark:text-gray-200">{source}</span>
        </div>
        {/* Display other properties if needed, or remove this part
        <h4 className="mt-3 font-semibold text-gray-700 dark:text-gray-300">All Properties:</h4>
        {Object.entries(properties)
          .filter(([key]) => !['name', 'ASSET_NAME', 'capacity_mw', 'source', 'commission_year', 'capacity_update_date'].includes(key))
          .map(([key, value]) => (
            <div key={key} className="flex justify-between">
              <span className="truncate pr-1">{key}:</span>
              <span className="truncate font-medium text-gray-800 dark:text-gray-200">{String(value)}</span>
            </div>
        ))}
        */}
      </div>
    </GlassContainer>
  );
}
