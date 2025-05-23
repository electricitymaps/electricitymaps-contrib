// Helper to get a color based on status - can be expanded
export const getStatusColor = (status: string | undefined) => {
  if (!status) {
    return 'bg-gray-400'; // Default grey for unknown for the circle
  }
  switch (status.toLowerCase()) {
    case 'operating':
    case 'operational':
    case 'commissioned': {
      return 'bg-green-500';
    } // Green for operational
    case 'planned': {
      return 'bg-blue-500';
    } // Blue for planned
    case 'construction': {
      return 'bg-yellow-500';
    } // Yellow for construction
    case 'cancelled':
    case 'retired': {
      return 'bg-red-500';
    } // Red for cancelled/retired
    default: {
      return 'bg-gray-400';
    } // Default grey for any other status
  }
};

export const MIN_ZOOM_FOR_ASSET_NAME_TOOLTIP = 2.4;
export const MIN_ZOOM_FOR_ASSET_SYMBOL_APPEARING = 5;
