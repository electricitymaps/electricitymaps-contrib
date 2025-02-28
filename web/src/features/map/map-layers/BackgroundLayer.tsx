import { useTheme } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import type { ReactElement } from 'react';
import { Layer } from 'react-map-gl/maplibre';
import { windOnlyModeAtom } from 'utils/state/atoms';

export default function BackgroundLayer(): ReactElement {
  const theme = useTheme();
  const windOnlyMode = useAtomValue(windOnlyModeAtom);

  // In wind-only mode, use a transparent background
  return (
    <Layer
      id="ocean"
      type="background"
      paint={{
        'background-color': windOnlyMode ? 'rgba(0,0,0,0)' : theme.oceanColor,
      }}
    />
  );
}
