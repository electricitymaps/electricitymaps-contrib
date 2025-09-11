import {
  isLayersModalOpenAtom,
  isSettingsModalOpenAtom,
} from 'features/modals/modalAtoms';
import { useSetAtom } from 'jotai';
import { LayersIcon, SettingsIcon } from 'lucide-react';
import { ReactElement, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { RouteParameters } from 'types';
import { useIsMobile } from 'utils/styling';

import { TooltipWrapperReference } from '../../components/tooltips/TooltipWrapper';
import MapButton from './MapButton';

export default function MapButtons(): ReactElement {
  const { t } = useTranslation();
  const setIsSettingsModalOpen = useSetAtom(isSettingsModalOpenAtom);
  const setIsLayersModalOpen = useSetAtom(isLayersModalOpenAtom);
  const { zoneId } = useParams<RouteParameters>();
  const isMobile = useIsMobile();

  // Refs for tooltip wrappers to be able to close them programmatically
  const settingsTooltipReference = useRef<TooltipWrapperReference | null>(null);
  const layersTooltipReference = useRef<TooltipWrapperReference | null>(null);

  const handleToggleSettingsModal = useCallback(
    (event: React.MouseEvent) => {
      event.stopPropagation();
      // Close the tooltip if it's open
      if (settingsTooltipReference.current) {
        settingsTooltipReference.current.close();
      }
      setIsSettingsModalOpen();
    },
    [setIsSettingsModalOpen]
  );

  const handleToggleLayersModal = useCallback(
    (event: React.MouseEvent) => {
      event.stopPropagation();
      // Close the tooltip if it's open
      if (layersTooltipReference.current) {
        layersTooltipReference.current.close();
      }
      setIsLayersModalOpen();
    },
    [setIsLayersModalOpen]
  );

  // Hide the layers button when on mobile and a zone is selected
  const shouldShowLayersButton = !(isMobile && zoneId);
  return (
    <div
      className={`pointer-events-none absolute right-3 z-20 mt-[max(0.75rem,env(safe-area-inset-top),var(--safe-area-inset-top))] flex flex-col items-end sm:top-3 sm:mt-0`}
    >
      <div className="pointer-events-auto flex flex-col gap-2">
        <MapButton
          icon={<SettingsIcon size={20} />}
          tooltipText={t('settings-modal.title')}
          onClick={handleToggleSettingsModal}
          dataTestId="settings-button"
          ariaLabel={t('aria.label.settings')}
          tooltipRef={settingsTooltipReference}
        />
        {shouldShowLayersButton && (
          <MapButton
            icon={<LayersIcon size={20} />}
            tooltipText={t('tooltips.layers')}
            onClick={handleToggleLayersModal}
            dataTestId="layers-button"
            ariaLabel={t('aria.label.layers')}
            tooltipRef={layersTooltipReference}
          />
        )}
      </div>
    </div>
  );
}
