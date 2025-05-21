import { useAtomValue } from 'jotai';

import { selectedSolarAssetAtom } from './mapAtoms';

export default function SolarAssetDataBox() {
  const selectedAsset = useAtomValue(selectedSolarAssetAtom);

  if (!selectedAsset) {
    return null;
  }

  const { properties } = selectedAsset;

  // Basic styling for the data box
  const style: React.CSSProperties = {
    position: 'absolute',
    top: '20px',
    right: '20px',
    width: '300px',
    maxHeight: '400px',
    overflowY: 'auto',
    backgroundColor: 'white',
    color: 'black',
    padding: '15px',
    borderRadius: '5px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
    zIndex: 999, // Below tooltip, but above map
  };

  return (
    <div style={style}>
      <h3>Solar Asset Details</h3>
      {/* Render properties as a simple list for now */}
      {Object.entries(properties).map(([key, value]) => (
        <div key={key}>
          <strong>{key}:</strong> {String(value)}
        </div>
      ))}
    </div>
  );
}
