import { useFeatureFlag } from 'features/feature-flags/api';
import { ReactElement } from 'react';
import { NavigationControl } from 'react-map-gl/maplibre';

export default function ZoomControls(): ReactElement {
  const isConsumptionOnlyMode = useFeatureFlag('consumption-only');
  const marginTop = isConsumptionOnlyMode ? 54 : 98;
  return (
    <NavigationControl
      style={{
        marginRight: 12,
        marginTop: `calc(${marginTop}px + env(safe-area-inset-top, 0px))`,
        width: '33px',
        boxShadow: '0px 1px 1px  rgb(0 0 0 / 0.1)',
        border: 0,
        color: 'white',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
      showCompass={false}
      //TODO: Find a way to use a __('tooltips.zoomIn') as aria-label here
      //TODO: Find a way to use a __('tooltips.zoomOut') as aria-label here
    />
  );
}
