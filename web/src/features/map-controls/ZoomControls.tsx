import { useFeatureFlag } from 'features/feature-flags/api';
import { useAtom } from 'jotai';
import { ReactElement } from 'react';
import { useMap } from 'react-map-gl/maplibre';
import { ToggleOptions } from 'utils/constants';
import { windLayerAtom, windOnlyModeAtom } from 'utils/state/atoms';

export default function ZoomControls(): ReactElement {
  const isConsumptionOnlyMode = useFeatureFlag('consumption-only');
  const marginTop = isConsumptionOnlyMode ? 54 : 98;
  const { current: map } = useMap();
  const [windOnlyMode, setWindOnlyMode] = useAtom(windOnlyModeAtom);
  const [windLayer, setWindLayer] = useAtom(windLayerAtom);

  const handleZoomIn = () => {
    map?.zoomIn();
  };

  const handleZoomOut = () => {
    map?.zoomOut();
  };

  const toggleWindOnlyMode = () => {
    // If wind layer is not enabled, enable it when entering wind-only mode
    if (!windLayer && !windOnlyMode) {
      setWindLayer(ToggleOptions.ON);
    }
    setWindOnlyMode(!windOnlyMode);
  };

  return (
    <div className="absolute bottom-4 right-4 z-10 flex flex-col gap-2">
      <button
        className="flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-md"
        onClick={handleZoomIn}
        aria-label="Zoom in"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 6v6m0 0v6m0-6h6m-6 0H6"
          />
        </svg>
      </button>
      <button
        className="flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-md"
        onClick={handleZoomOut}
        aria-label="Zoom out"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20 12H4"
          />
        </svg>
      </button>
      <button
        className={`flex h-10 w-10 items-center justify-center rounded-full shadow-md ${
          windOnlyMode ? 'bg-blue-500 text-white' : 'bg-white'
        }`}
        onClick={toggleWindOnlyMode}
        aria-label={windOnlyMode ? 'Exit wind-only mode' : 'Enter wind-only mode'}
        title={windOnlyMode ? 'Exit wind-only mode' : 'Enter wind-only mode'}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"
          />
        </svg>
      </button>
    </div>
  );
}
