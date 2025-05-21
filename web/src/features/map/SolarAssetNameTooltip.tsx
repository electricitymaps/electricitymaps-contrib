import { useAtomValue } from 'jotai';

import { hoveredSolarAssetInfoAtom, mapZoomAtom } from './mapAtoms';

const MIN_ZOOM_FOR_ASSET_NAME_TOOLTIP = 2.4; // Lowered zoom requirement

export default function SolarAssetNameTooltip() {
  const hoveredAssetInfo = useAtomValue(hoveredSolarAssetInfoAtom);
  const currentZoom = useAtomValue(mapZoomAtom);

  console.log('[SolarAssetNameTooltip] Hovered Asset Info:', hoveredAssetInfo);
  console.log('[SolarAssetNameTooltip] Current Zoom:', currentZoom);
  console.log(
    '[SolarAssetNameTooltip] Min Zoom for Tooltip:',
    MIN_ZOOM_FOR_ASSET_NAME_TOOLTIP
  );

  const shouldHideTooltip =
    !hoveredAssetInfo || currentZoom < MIN_ZOOM_FOR_ASSET_NAME_TOOLTIP;
  console.log(
    '[SolarAssetNameTooltip] Should hide tooltip? (condition is true if hiding):',
    shouldHideTooltip
  );

  if (shouldHideTooltip) {
    return null;
  }

  // This part will only be reached if shouldHideTooltip is false
  const { properties, x, y } = hoveredAssetInfo; // TS knows hoveredAssetInfo is not null here
  const assetName = properties.name || 'Unnamed Asset'; // Changed from properties.ASSET_NAME to properties.name
  console.log('[SolarAssetNameTooltip] Asset Name for tooltip:', assetName);
  console.log('[SolarAssetNameTooltip] Coordinates (x, y):', x, y);

  // Basic styling for the tooltip
  const style: React.CSSProperties = {
    position: 'absolute',
    left: x + 15, // Offset from cursor
    top: y + 15, // Offset from cursor
    backgroundColor: 'white',
    color: 'black',
    padding: '5px 10px',
    borderRadius: '3px',
    boxShadow: '0 0 5px rgba(0,0,0,0.3)',
    zIndex: 1000, // Ensure it's above other map elements
    pointerEvents: 'none', // So it doesn't interfere with map interactions
  };

  return <div style={style}>{assetName}</div>;
}
