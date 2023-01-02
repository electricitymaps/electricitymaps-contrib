import { Button } from 'components/Button';
import Modal from 'components/Modal';
import ConsumptionProductionToggle from 'features/map-controls/ConsumptionProductionToggle';
import LanguageSelector from 'features/map-controls/LanguageSelector';
import { weatherButtonMap } from 'features/map-controls/MapControls';
import SpatialAggregatesToggle from 'features/map-controls/SpatialAggregatesToggle';
import { useAtom } from 'jotai';
import { useState } from 'react';
import { HiOutlineEyeOff } from 'react-icons/hi';
import { HiLanguage } from 'react-icons/hi2';
import { MoonLoader } from 'react-spinners';
import { useTranslation } from 'translation/translation';
import { TimeAverages, ToggleOptions } from 'utils/constants';
import { selectedDatetimeIndexAtom, timeAverageAtom } from 'utils/state/atoms';
import { isSettingsModalOpenAtom } from './modalAtoms';

function WeatherToggleButton({
  allowed,
  type,
}: {
  allowed: boolean;
  type: 'wind' | 'solar';
}) {
  const { __ } = useTranslation();
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
      {!allowed && (
        <p className="text-sm italic text-red-400">{__(`${type}DataError`)}</p>
      )}

      <Button
        onClick={!isLoadingLayer ? onToggle : () => {}}
        textColor={isEnabled ? '#000' : '#999'}
        disabled={!allowed}
        icon={
          isLoadingLayer ? (
            <MoonLoader size={14} color="#135836" className="mr-1" />
          ) : (
            <Icon
              size={weatherButtonMap[type].iconSize}
              color={isEnabled ? '' : 'gray'}
            />
          )
        }
      >
        {__(
          isEnabled
            ? `tooltips.hide${typeAsTitlecase}Layer`
            : `tooltips.show${typeAsTitlecase}Layer`
        )}
      </Button>
    </>
  );
}

export function SettingsModalContent() {
  const [isLanguageSelectorOpen, setIsLanguageSelectorOpen] = useState(false);
  const [timeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);

  // We are currently only supporting and fetching weather data for the latest hourly value
  const areWeatherLayersAllowed =
    selectedDatetime.index === 24 && timeAverage === TimeAverages.HOURLY;

  const { __ } = useTranslation();
  return (
    <div className="flex flex-col items-center space-y-4">
      <ConsumptionProductionToggle />
      <SpatialAggregatesToggle />
      <Button
        onClick={() => setIsLanguageSelectorOpen(!isLanguageSelectorOpen)}
        icon={<HiLanguage size={21} />}
      >
        {__('tooltips.selectLanguage')}
      </Button>
      {isLanguageSelectorOpen && (
        <LanguageSelector
          className="top-[185px] left-auto right-auto z-10 mt-4 w-60 overflow-x-hidden shadow-lg sm:top-[200px]"
          setLanguageSelectorOpen={setIsLanguageSelectorOpen}
        />
      )}

      <WeatherToggleButton allowed={areWeatherLayersAllowed} type="wind" />
      <WeatherToggleButton allowed={areWeatherLayersAllowed} type="solar" />
      <Button onClick={() => {}} icon={<HiOutlineEyeOff size={21} />}>
        {__('legends.colorblindmode')}
      </Button>
    </div>
  );
}

export default function SettingsModal() {
  const { __ } = useTranslation();
  const [isOpen, setIsOpen] = useAtom(isSettingsModalOpenAtom);
  return (
    <Modal isOpen={isOpen} setIsOpen={setIsOpen} title={__('settings-modal.title')}>
      <SettingsModalContent />
    </Modal>
  );
}
