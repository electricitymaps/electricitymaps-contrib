import { Button } from 'components/Button';
import Modal from 'components/Modal';
import ConsumptionProductionToggle from 'features/map-controls/ConsumptionProductionToggle';
import { LanguageSelector } from 'features/map-controls/LanguageSelector';
import { weatherButtonMap } from 'features/map-controls/MapControls';
import SpatialAggregatesToggle from 'features/map-controls/SpatialAggregatesToggle';
import ThemeSelector from 'features/map-controls/ThemeSelector';
import { useAtom, useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { HiOutlineEyeOff } from 'react-icons/hi';
import { MoonLoader } from 'react-spinners';
import { ToggleOptions } from 'utils/constants';
import {
  colorblindModeAtom,
  isHourlyAtom,
  selectedDatetimeIndexAtom,
} from 'utils/state/atoms';

import { isSettingsModalOpenAtom } from './modalAtoms';

function WeatherToggleButton({
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

  const onToggle = () => {
    if (!isEnabled) {
      setIsLoadingLayer(true);
    }
    setEnabled(isEnabled ? ToggleOptions.OFF : ToggleOptions.ON);
  };

  return (
    <>
      {!allowed && <p className="text-sm italic text-red-400">{t(`${type}DataError`)}</p>}

      <Button
        onClick={isLoadingLayer ? () => {} : onToggle}
        size="lg"
        type={isEnabled ? 'primary' : 'secondary'}
        disabled={!allowed}
        backgroundClasses="w-[330px] h-[45px]"
        icon={
          isLoadingLayer ? (
            <MoonLoader size={14} color="white" className="mr-1" />
          ) : (
            <Icon size={weatherButtonMap[type].iconSize} />
          )
        }
      >
        {t(
          isEnabled
            ? `tooltips.hide${typeAsTitlecase}Layer`
            : `tooltips.show${typeAsTitlecase}Layer`
        )}
      </Button>
    </>
  );
}

export function SettingsModalContent() {
  const isHourly = useAtomValue(isHourlyAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [isColorblindModeEnabled, setIsColorblindModeEnabled] =
    useAtom(colorblindModeAtom);

  // We are currently only supporting and fetching weather data for the latest hourly value
  const areWeatherLayersAllowed = selectedDatetime.index === 24 && isHourly;

  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center space-y-2">
      <div className="rounded-full bg-gray-500">
        <ConsumptionProductionToggle />
      </div>
      <div className="rounded-full bg-gray-500">
        <SpatialAggregatesToggle />
      </div>
      <LanguageSelector isMobile />
      <WeatherToggleButton allowed={areWeatherLayersAllowed} type="wind" />
      <WeatherToggleButton allowed={areWeatherLayersAllowed} type="solar" />
      <Button
        size="lg"
        type={isColorblindModeEnabled ? 'primary' : 'secondary'}
        backgroundClasses="w-[330px] h-[45px]"
        onClick={() => setIsColorblindModeEnabled(!isColorblindModeEnabled)}
        icon={<HiOutlineEyeOff size={21} />}
      >
        {t('legends.colorblindmode')}
      </Button>
      <ThemeSelector isMobile />
    </div>
  );
}

export default function SettingsModal() {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useAtom(isSettingsModalOpenAtom);
  return (
    <Modal isOpen={isOpen} setIsOpen={setIsOpen} title={t('settings-modal.title')}>
      <SettingsModalContent />
    </Modal>
  );
}
