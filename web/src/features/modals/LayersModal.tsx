import * as Dialog from '@radix-ui/react-dialog';
import GlassContainer from 'components/GlassContainer';
import SwitchToggle from 'components/ToggleSwitch';
import { weatherButtonMap } from 'features/map-controls/MapControls';
import { useDarkMode } from 'hooks/theme';
import { useAtom, useAtomValue } from 'jotai';
import { XIcon } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { MoonLoader } from 'react-spinners';
import { ToggleOptions } from 'utils/constants';
import { areWeatherLayersAllowedAtom } from 'utils/state/atoms';

import { isLayersModalOpenAtom } from './modalAtoms';

function WeatherToggleSwitch({
  allowed,
  type,
}: {
  allowed: boolean;
  type: 'wind' | 'solar';
}) {
  const { t } = useTranslation();
  const [enabled, setEnabled] = useAtom(weatherButtonMap[type].enabledAtom);
  const [isLoadingLayer, setIsLoadingLayer] = useAtom(weatherButtonMap[type].loadingAtom);
  const isEnabled = enabled === ToggleOptions.ON;
  const Icon = weatherButtonMap[type].icon;
  const typeAsTitlecase = type.charAt(0).toUpperCase() + type.slice(1);
  const isDarkModeEnabled = useDarkMode();
  const onToggle = (newEnabled: boolean) => {
    if (newEnabled) {
      setIsLoadingLayer(true);
    }
    setEnabled(newEnabled ? ToggleOptions.ON : ToggleOptions.OFF);
  };

  return (
    <div className="flex w-full items-center justify-between p-3">
      <div className="flex items-center">
        <Icon size={20} className="mr-2 text-secondary dark:text-secondary-dark" />
        <span className="text-sm font-medium text-secondary dark:text-secondary-dark">
          {t(`aria.label.${type}Layer`)}
        </span>
      </div>

      <div className="relative">
        <SwitchToggle
          isEnabled={isEnabled}
          onChange={!allowed || isLoadingLayer ? () => {} : onToggle}
          className={` ${
            !allowed || isLoadingLayer ? 'cursor-not-allowed opacity-50' : ''
          }`}
          ariaLabel={t(`Toggle ${typeAsTitlecase} layer`)}
        />
        {isLoadingLayer && (
          <span className="absolute inset-0 mb-[6px] ml-4 flex items-center justify-center">
            <MoonLoader size={10} color={isDarkModeEnabled ? 'white' : 'black'} />
          </span>
        )}
      </div>
    </div>
  );
}

export function LayersModalContent() {
  const areWeatherLayersAllowed = useAtomValue(areWeatherLayersAllowedAtom);

  return (
    <div className="p-2">
      <WeatherToggleSwitch allowed={areWeatherLayersAllowed} type="wind" />
      <WeatherToggleSwitch allowed={areWeatherLayersAllowed} type="solar" />
      {!areWeatherLayersAllowed && (
        <p className="px-4 py-2 text-sm text-secondary dark:text-secondary-dark">
          Weather data not available for this aggregation, switch to real-time to see live
          weather data
        </p>
      )}
    </div>
  );
}

function MobileDismissButton({ onClick }: { onClick: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="absolute inset-x-0 top-36 mx-auto flex justify-center md:hidden">
      <GlassContainer className="flex h-9 w-9 items-center justify-center rounded-full ">
        <button aria-label={t('misc.dismiss')} onClick={onClick}>
          <XIcon size={20} />
        </button>
      </GlassContainer>
    </div>
  );
}

export default function LayersModal() {
  const [isOpen, setIsOpen] = useAtom(isLayersModalOpenAtom);

  if (!isOpen) {
    return null;
  }

  const handleClose = () => {
    setIsOpen(false);
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={setIsOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 md:bg-transparent" />
        <Dialog.Content
          onOpenAutoFocus={(event: Event) => event.preventDefault()}
          className="pointer-events-auto fixed inset-0 z-[51] overflow-auto"
          onClick={(event_) => {
            if (event_.target === event_.currentTarget) {
              handleClose();
            }
          }}
        >
          <div className="pointer-events-auto absolute inset-x-0 top-3 mt-[env(safe-area-inset-top)] flex justify-center md:inset-x-auto md:right-72 md:mr-14 md:justify-start">
            <GlassContainer className="w-full max-w-xs rounded-xl shadow-lg md:w-72">
              <LayersModalContent />
            </GlassContainer>
          </div>

          <div className="pointer-events-auto">
            <MobileDismissButton onClick={handleClose} />
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
