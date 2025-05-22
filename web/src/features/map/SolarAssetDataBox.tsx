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
    return 'bg-gray-400';
  } // Default
  switch (status.toLowerCase()) {
    case 'operating':
    case 'operational':
    case 'commissioned': {
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
    <GlassContainer className="pointer-events-auto absolute right-5 top-5 z-[999] flex w-96 flex-col p-4 shadow-lg">
      {/* Energy Type Tag - Status badge was removed from this line */}
      <div className="mb-2 flex items-center justify-between">
        <span
          className={`inline-block rounded-full bg-yellow-500 px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider text-white`}
        >
          Solar
        </span>
        {/* Status badge was correctly removed from here previously */}
      </div>

      {/* Header with Name, Icon and Close Button */}
      <div className="mb-1 flex items-start justify-between">
        <div className="flex items-center">
          <img src="/images/solar_asset.png" alt="Solar Asset" className="mr-2 h-6 w-6" />
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
          <span
            className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold uppercase tracking-wider text-white ${getStatusColor(
              status
            )}`}
          >
            {status}
          </span>
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
