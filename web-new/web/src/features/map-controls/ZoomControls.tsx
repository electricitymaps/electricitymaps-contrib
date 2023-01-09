import { ReactElement } from 'react';
import { NavigationControl } from 'react-map-gl';

export default function ZoomControls(): ReactElement {
  return (
    <NavigationControl
      style={{
        marginRight: 12,
        marginTop: 98,
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
