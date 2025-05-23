import { useAtomValue } from 'jotai';

import { getStatusColor } from '../assets/utils';
import { hoveredSolarAssetInfoAtom, mapZoomAtom } from './mapAtoms';

const MIN_ZOOM_FOR_ASSET_NAME_TOOLTIP = 2.4;

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
      status = 'Operational';
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
      className="pointer-events-none z-[1000] flex w-max min-w-[150px] flex-col gap-1 rounded-md bg-white p-2 text-xs shadow-lg dark:bg-gray-800" // Use text-xs for tooltip, added w-max and min-w
    >
      {/* Solar Tag with Icon */}
      <div className="mb-1 self-start">
        <span
          className={`inline-flex items-center rounded-full bg-yellow-500 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-white`}
        >
          <img src="/images/solar_asset.png" alt="Solar" className="mr-1 h-3 w-3" />
          Solar
        </span>
      </div>

      {/* Asset Name - Icon removed from here */}
      <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
        {assetName}
      </div>

      {/* Status and Capacity line */}
      <div className="flex items-center gap-2 text-[11px]">
        {' '}
        {/* Adjusted overall text size for this line */}
        {/* Status with colored circle */}
        <div className="flex items-center">
          <span
            className={`mr-1 h-2 w-2 rounded-full ${getStatusColor(status)}`}
            aria-hidden="true"
          />
          <span className="text-gray-700 dark:text-gray-300">{status}</span>
        </div>
        {!Number.isNaN(capacityMw) && (
          <span className="text-gray-700 dark:text-gray-300">
            &#8226; {`${capacityMw.toFixed(1)} MW`}
          </span>
        )}
      </div>
    </div>
  );
}
