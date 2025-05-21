import GlassContainer from 'components/GlassContainer'; // Import GlassContainer
import { useAtomValue, useSetAtom } from 'jotai';
// import { XMarkIcon } from '@heroicons/react/24/solid'; // For the close button
import { X } from 'lucide-react'; // Using Lucide X icon

import { selectedSolarAssetAtom } from './mapAtoms';

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

  // Basic styling for the data box - REPLACED WITH TAILWIND + GlassContainer
  // const style: React.CSSProperties = {
  //   position: 'absolute',
  //   top: '20px',
  //   right: '20px',
  //   width: '300px',
  //   maxHeight: '400px',
  //   overflowY: 'auto',
  //   backgroundColor: 'white',
  //   color: 'black',
  //   padding: '15px',
  //   borderRadius: '5px',
  //   boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
  //   zIndex: 999, // Below tooltip, but above map
  // };

  return (
    <GlassContainer className="pointer-events-auto absolute right-5 top-5 z-[999] flex w-80 flex-col p-4 shadow-lg">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
          Solar Asset Details
        </h3>
        <button
          onClick={handleClose}
          className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          aria-label="Close"
        >
          {/* <XMarkIcon className="h-6 w-6" /> */}
          <X className="h-6 w-6" /> {/* Using Lucide X icon */}
        </button>
      </div>
      <div className="max-h-80 overflow-y-auto text-sm text-gray-700 dark:text-gray-300">
        {/* Render properties as a simple list for now */}
        {Object.entries(properties).map(([key, value]) => (
          <div
            key={key}
            className="mb-1 border-b border-gray-200 pb-1 dark:border-gray-700"
          >
            <strong className="font-medium text-gray-900 dark:text-gray-100">
              {key}:
            </strong>{' '}
            {String(value)}
          </div>
        ))}
      </div>
    </GlassContainer>
  );
}
