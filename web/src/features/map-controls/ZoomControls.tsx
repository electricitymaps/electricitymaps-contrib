
import { ReactElement, useEffect, useState } from 'react';
import { NavigationControl } from 'react-map-gl/maplibre';

export default function ZoomControls(): ReactElement {
  const [topMargin, setTopMargin] = useState(98);
  useEffect(() => {
    const updateTopMargin = () => {
      const safeAreaTop =
        Number.parseInt(
          getComputedStyle(document.documentElement).getPropertyValue('--sat'),
          10
        ) || 0;
      setTopMargin(98 + safeAreaTop);
    };

    updateTopMargin();
    window.addEventListener('resize', updateTopMargin);
    return () => window.removeEventListener('resize', updateTopMargin);
  }, []);


  return (
    <NavigationControl
      style={{
        marginRight: 12,
        marginTop: topMargin,
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
