import { useAtom } from 'jotai';
import { ReactElement, useCallback, useState } from 'react';
import { useMap } from 'react-map-gl/maplibre';
import { ToggleOptions } from 'utils/constants';
import { windLayerAtom, windOnlyModeAtom } from 'utils/state/atoms';

export default function WindOnlyModeToggle(): ReactElement {
  const [windOnlyMode, setWindOnlyMode] = useAtom(windOnlyModeAtom);
  const [windLayer, setWindLayer] = useAtom(windLayerAtom);
  const [showExportOptions, setShowExportOptions] = useState(false);
  const { current: map } = useMap();

  const toggleWindOnlyMode = () => {
    // If wind layer is not enabled, enable it when entering wind-only mode
    if (!windLayer && !windOnlyMode) {
      setWindLayer(ToggleOptions.ON);
    }
    setWindOnlyMode(!windOnlyMode);
    setShowExportOptions(false);
  };

  const exportAsVectorSvg = useCallback(() => {
    // Find the wind canvas element
    const windCanvas = document.querySelector('#wind') as HTMLCanvasElement;
    if (!windCanvas) {
      console.error('Wind canvas not found');
      return;
    }

    try {
      // Create an SVG element with the same dimensions as the canvas
      const svgNS = 'http://www.w3.org/2000/svg';
      const svg = document.createElementNS(svgNS, 'svg');
      svg.setAttribute('width', windCanvas.width.toString());
      svg.setAttribute('height', windCanvas.height.toString());
      svg.setAttribute('viewBox', `0 0 ${windCanvas.width} ${windCanvas.height}`);

      // Add a white background rectangle
      const background = document.createElementNS(svgNS, 'rect');
      background.setAttribute('width', '100%');
      background.setAttribute('height', '100%');
      background.setAttribute('fill', 'white');
      background.setAttribute('fill-opacity', '0'); // Transparent background
      svg.append(background);

      // Try to access the Windy instance to get the wind field data
      // This is a bit hacky as we're accessing a private variable
      // @ts-ignore - Accessing windySingleton from the global scope
      const windySingleton = window.windySingleton;

      if (windySingleton && windySingleton.field) {
        // We have access to the wind field data, so we can create vector paths
        const field = windySingleton.field;
        const bounds = field.bounds;
        const particleGroup = document.createElementNS(svgNS, 'g');
        particleGroup.setAttribute('stroke-linecap', 'round');

        // Create a set of streamlines based on the current particle positions
        // Sample the wind field at regular intervals
        const sampleStep = 10; // pixels
        const streamlineLength = 20; // steps

        for (let x = bounds.x; x < bounds.x + bounds.width; x += sampleStep) {
          for (let y = bounds.y; y < bounds.y + bounds.height; y += sampleStep) {
            // Start a streamline at this point
            let currentX = x;
            let currentY = y;
            let isValidStreamline = true;

            // Create a path for this streamline
            const path = document.createElementNS(svgNS, 'path');
            let pathData = `M${currentX},${currentY}`;

            // Follow the wind vector for several steps
            for (let step = 0; step < streamlineLength; step++) {
              const windVector = field.getWind(currentX, currentY);

              // Check if we have a valid wind vector
              if (!windVector || windVector[2] === null || Number.isNaN(windVector[2])) {
                isValidStreamline = false;
                break;
              }

              // Get the wind direction and magnitude
              const u = windVector[0]; // x component
              const v = windVector[1]; // y component
              const magnitude = windVector[2];

              // Skip if magnitude is too small
              if (magnitude < 0.1) {
                isValidStreamline = false;
                break;
              }

              // Move in the direction of the wind
              currentX += u;
              currentY += v;

              // Add a line segment to the path
              pathData += ` L${currentX},${currentY}`;

              // Check if we're still within bounds
              if (
                currentX < bounds.x ||
                currentX > bounds.x + bounds.width ||
                currentY < bounds.y ||
                currentY > bounds.y + bounds.height
              ) {
                break;
              }
            }

            // Only add valid streamlines
            if (isValidStreamline) {
              path.setAttribute('d', pathData);
              path.setAttribute('fill', 'none');
              path.setAttribute('stroke', 'rgba(70, 130, 180, 0.7)'); // Steel blue with transparency
              path.setAttribute('stroke-width', '1');
              particleGroup.append(path);
            }
          }
        }

        svg.append(particleGroup);

        // Convert the SVG to a string
        const serializer = new XMLSerializer();
        const svgString = serializer.serializeToString(svg);

        // Create a Blob from the SVG string
        const blob = new Blob([svgString], { type: 'image/svg+xml' });

        // Create a download link
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'wind-map-vector.svg';

        // Trigger the download
        document.body.append(link);
        link.click();

        // Clean up
        link.remove();
        URL.revokeObjectURL(url);
      } else {
        console.error('Wind field data not available for vector export');
        alert('Vector export failed. Please try raster export instead.');
      }
    } catch (error) {
      console.error('Error exporting vector SVG:', error);
      alert('Vector export failed. Please try raster export instead.');
    }

    setShowExportOptions(false);
  }, []);

  const exportAsRasterSvg = useCallback(() => {
    // Find the wind canvas element
    const windCanvas = document.querySelector('#wind') as HTMLCanvasElement;
    if (!windCanvas) {
      console.error('Wind canvas not found');
      return;
    }

    try {
      // Create an SVG element with the same dimensions as the canvas
      const svgNS = 'http://www.w3.org/2000/svg';
      const svg = document.createElementNS(svgNS, 'svg');
      svg.setAttribute('width', windCanvas.width.toString());
      svg.setAttribute('height', windCanvas.height.toString());
      svg.setAttribute('viewBox', `0 0 ${windCanvas.width} ${windCanvas.height}`);

      // Create a foreign object to embed the canvas as an image
      const foreignObject = document.createElementNS(svgNS, 'foreignObject');
      foreignObject.setAttribute('width', '100%');
      foreignObject.setAttribute('height', '100%');

      // Convert canvas to data URL
      const dataURL = windCanvas.toDataURL('image/png');

      // Create an image element with the data URL
      const img = document.createElementNS('http://www.w3.org/1999/xhtml', 'img');
      img.setAttribute('src', dataURL);
      img.setAttribute('width', '100%');
      img.setAttribute('height', '100%');

      // Append the image to the foreign object
      foreignObject.append(img);

      // Append the foreign object to the SVG
      svg.append(foreignObject);

      // Convert the SVG to a string
      const serializer = new XMLSerializer();
      const svgString = serializer.serializeToString(svg);

      // Create a Blob from the SVG string
      const blob = new Blob([svgString], { type: 'image/svg+xml' });

      // Create a download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'wind-map-raster.svg';

      // Trigger the download
      document.body.append(link);
      link.click();

      // Clean up
      link.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting raster SVG:', error);

      // Fallback to a simple PNG if all else fails
      try {
        const dataURL = windCanvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.href = dataURL;
        link.download = 'wind-map.png';
        document.body.append(link);
        link.click();
        link.remove();
      } catch (fallbackError) {
        console.error('Error with fallback export:', fallbackError);
        alert('Export failed. Please try again or take a screenshot instead.');
      }
    }

    setShowExportOptions(false);
  }, []);

  const exportAsPng = useCallback(() => {
    // Find the wind canvas element
    const windCanvas = document.querySelector('#wind') as HTMLCanvasElement;
    if (!windCanvas) {
      console.error('Wind canvas not found');
      return;
    }

    try {
      const dataURL = windCanvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.href = dataURL;
      link.download = 'wind-map.png';
      document.body.append(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting PNG:', error);
      alert('PNG export failed. Please try taking a screenshot instead.');
    }

    setShowExportOptions(false);
  }, []);

  return (
    <div className="absolute right-4 top-4 z-50 flex flex-col gap-2">
      <button
        className={`flex items-center justify-center rounded-md px-4 py-2 shadow-md ${
          windOnlyMode ? 'bg-blue-500 text-white' : 'bg-white'
        }`}
        onClick={toggleWindOnlyMode}
        aria-label={windOnlyMode ? 'Exit wind-only mode' : 'Enter wind-only mode'}
        title={windOnlyMode ? 'Exit wind-only mode' : 'Enter wind-only mode'}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="mr-2 h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 11l3-3m0 0l3 3m-3-3v8m0-13a9 9 0 110 18 9 9 0 010-18z"
          />
        </svg>
        {windOnlyMode ? 'Exit Wind Only Mode' : 'Wind Only Mode'}
      </button>

      {windOnlyMode && !showExportOptions && (
        <button
          className="flex items-center justify-center rounded-md bg-green-500 px-4 py-2 text-white shadow-md"
          onClick={() => setShowExportOptions(true)}
          aria-label="Export Options"
          title="Export Options"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="mr-2 h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          Export Options
        </button>
      )}

      {windOnlyMode && showExportOptions && (
        <div className="flex flex-col gap-2 rounded-md bg-white p-2 shadow-md">
          <button
            className="flex items-center justify-center rounded-md bg-blue-500 px-4 py-2 text-white shadow-md"
            onClick={exportAsVectorSvg}
            aria-label="Export as Vector SVG"
            title="Export as Vector SVG (best for editing)"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="mr-2 h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
              />
            </svg>
            Vector SVG
          </button>

          <button
            className="flex items-center justify-center rounded-md bg-purple-500 px-4 py-2 text-white shadow-md"
            onClick={exportAsRasterSvg}
            aria-label="Export as Raster SVG"
            title="Export as Raster SVG (exact appearance)"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="mr-2 h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            Raster SVG
          </button>

          <button
            className="flex items-center justify-center rounded-md bg-green-500 px-4 py-2 text-white shadow-md"
            onClick={exportAsPng}
            aria-label="Export as PNG"
            title="Export as PNG (most compatible)"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="mr-2 h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
            PNG Image
          </button>

          <button
            className="flex items-center justify-center rounded-md bg-gray-300 px-4 py-2 text-gray-700 shadow-md"
            onClick={() => setShowExportOptions(false)}
            aria-label="Cancel"
            title="Cancel"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="mr-2 h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
