import GlassContainer from 'components/GlassContainer';
import SwitchToggle from 'components/ToggleSwitch';
import { weatherButtonMap } from 'features/map-controls/MapControls';
import { useDarkMode } from 'hooks/theme';
import { useAtom, useAtomValue } from 'jotai';
import { useEffect, useRef } from 'react';
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
          {t(`${typeAsTitlecase} layer`)}
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

export default function LayersModal() {
  const [isOpen, setIsOpen] = useAtom(isLayersModalOpenAtom);
  const modalReference = useRef<HTMLDivElement>(null);

  // Handle click outside to close modal
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      // Check if the event target is a button with layers-button data-testid
      const isLayersButton = (event.target as Element)?.closest(
        '[data-testid="layers-button"]'
      );

      // Don't close if clicking the layers button - let the toggle handler manage it
      if (isLayersButton) {
        return;
      }

      if (
        modalReference.current &&
        !modalReference.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside, true);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside, true);
    };
  }, [isOpen, setIsOpen]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="absolute right-72 top-3 z-30 mr-14 mt-[env(safe-area-inset-top)]">
      <GlassContainer
        ref={modalReference}
        className="w-72 overflow-hidden rounded-xl shadow-lg"
      >
        <LayersModalContent />
      </GlassContainer>
    </div>
  );
}
