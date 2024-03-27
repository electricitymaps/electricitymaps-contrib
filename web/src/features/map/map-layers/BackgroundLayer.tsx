import { useTheme } from 'hooks/theme';
import type { ReactElement } from 'react';
import { Layer } from 'react-map-gl/maplibre';

export default function BackgroundLayer(): ReactElement {
  const theme = useTheme();
  return (
    <Layer
      id="ocean"
      type="background"
      paint={{ 'background-color': theme.oceanColor }}
    />
  );
}
