import { Button } from 'components/Button';
import { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import { FaMinus, FaPlus } from 'react-icons/fa6';
import { useMap } from 'react-map-gl/maplibre';

export default function ZoomControls(): ReactElement {
  const { map } = useMap();
  const { t } = useTranslation();
  return (
    <div className="flex flex-col">
      <Button
        size="md"
        icon={<FaPlus size={20} />}
        onClick={() => map?.zoomIn()}
        ariaLabel={t('tooltips.zoomIn')}
        type="opaque"
        dataTestId="zoom-in"
        backgroundClasses="rounded-none rounded-t-full"
        foregroundClasses="rounded-none rounded-t-full"
      />
      <Button
        size="md"
        icon={<FaMinus size={20} />}
        onClick={() => map?.zoomOut()}
        ariaLabel={t('tooltips.zoomOut')}
        type="opaque"
        dataTestId="zoom-out"
        backgroundClasses="rounded-none rounded-b-full"
        foregroundClasses="rounded-none rounded-b-full"
      />
    </div>
  );
}
