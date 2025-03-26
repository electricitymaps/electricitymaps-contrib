import {
  isLayersModalOpenAtom,
  isSettingsModalOpenAtom,
} from 'features/modals/modalAtoms';
import { useSetAtom } from 'jotai';
import { LayersIcon, SettingsIcon } from 'lucide-react';
import { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';

import MapButton from './MapButton';

export default function MapButtons(): ReactElement {
  const { t } = useTranslation();
  const setIsSettingsModalOpen = useSetAtom(isSettingsModalOpenAtom);
  const setIsLayersModalOpen = useSetAtom(isLayersModalOpenAtom);

  const handleToggleSettingsModal = (event: React.MouseEvent) => {
    event.stopPropagation();
    setIsSettingsModalOpen();
  };

  const handleToggleLayersModal = (event: React.MouseEvent) => {
    event.stopPropagation();
    setIsLayersModalOpen();
  };

  return (
    <div className="pointer-events-none absolute right-3 top-3 z-20 mt-[env(safe-area-inset-top)] flex flex-col items-end">
      <div className="pointer-events-auto flex flex-col gap-2">
        <MapButton
          icon={<SettingsIcon size={20} />}
          tooltipText={t('tooltips.settings')}
          onClick={handleToggleSettingsModal}
          dataTestId="settings-button"
          ariaLabel={t('aria.label.settings')}
        />
        <MapButton
          icon={<LayersIcon size={20} />}
          tooltipText={t('tooltips.layers')}
          onClick={handleToggleLayersModal}
          dataTestId="layers-button"
          ariaLabel={t('aria.label.layers')}
        />
      </div>
    </div>
  );
}
