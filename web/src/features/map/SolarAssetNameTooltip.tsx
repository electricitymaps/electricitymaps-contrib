import { useAtomValue } from 'jotai';

import { hoveredSolarAssetInfoAtom, mapZoomAtom } from './mapAtoms';

const MIN_ZOOM_FOR_ASSET_NAME_TOOLTIP = 2.4;

// Helper to get a color based on status - can be expanded
// Copied from SolarAssetDataBox.tsx - consider moving to a shared util if used more widely
const getStatusColor = (status: string | undefined) => {
  if (!status) {
    return 'bg-gray-400';
  } // Default
  switch (status.toLowerCase()) {
    case 'operating':
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

export default function SolarAssetNameTooltip() {
  const hoveredAssetInfo = useAtomValue(hoveredSolarAssetInfoAtom);
  const currentZoom = useAtomValue(mapZoomAtom);

  const shouldHideTooltip =
    !hoveredAssetInfo || currentZoom < MIN_ZOOM_FOR_ASSET_NAME_TOOLTIP;

  if (shouldHideTooltip) {
    return null;
  }

  const { properties, x, y } = hoveredAssetInfo;
  const assetName = properties.name || properties.ASSET_NAME || 'Unnamed Asset';
  const capacityMw = Number.parseFloat(String(properties.capacity_mw));
  const commissionYear = properties.commission_year
    ? String(Math.floor(Number(properties.commission_year)))
    : null;

  let status = properties.status ? String(properties.status) : 'Unknown';

  // Infer status if commission year is in the past and status is Unknown
  if (commissionYear) {
    const numericCommissionYear = Number.parseInt(commissionYear, 10);
    const currentYear = new Date().getFullYear();
    if (
      !Number.isNaN(numericCommissionYear) &&
      numericCommissionYear <= currentYear &&
      status.toLowerCase() === 'unknown'
    ) {
      status = 'Commissioned';
    }
  }

  return (
    <div
      style={{
        position: 'absolute',
        left: x + 15, // Offset from cursor
        top: y + 15, // Offset from cursor
        transform: 'translateY(-100%)', // Position tooltip above cursor
      }}
      className="pointer-events-none z-[1000] flex flex-col gap-1 rounded-md bg-white p-2 text-sm shadow-lg dark:bg-gray-800"
    >
      <div className="font-semibold text-gray-900 dark:text-gray-100">{assetName}</div>
      <div className="flex items-center gap-2">
        <span
          className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold uppercase tracking-wider text-white ${getStatusColor(
            status
          )}`}
        >
          {status}
        </span>
        {!Number.isNaN(capacityMw) && (
          <span className="text-xs text-gray-700 dark:text-gray-300">
            {`${capacityMw.toFixed(1)} MW`}
          </span>
        )}
      </div>
    </div>
  );
}
