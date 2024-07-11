import { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import { FaMinus, FaPlus } from 'react-icons/fa6';
import { useMap } from 'react-map-gl/maplibre';

import MapButton from './MapButton';

export default function ZoomControls(): ReactElement {
  const { map } = useMap();
  const { t } = useTranslation();
  return (
    <>
      <MapButton
        icon={<FaPlus size={20} />}
        onClick={() => map?.zoomIn()}
        ariaLabel={t('tooltips.zoomIn')}
        dataTestId="zoom-in"
      />
      <MapButton
        icon={<FaMinus size={20} />}
        onClick={() => map?.zoomOut()}
        ariaLabel={t('tooltips.zoomOut')}
        dataTestId="zoom-out"
      />
    </>
  );
}
