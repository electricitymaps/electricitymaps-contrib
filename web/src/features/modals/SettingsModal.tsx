import { Button } from 'components/Button';
import Modal from 'components/Modal';
import ConsumptionProductionToggle from 'features/map-controls/ConsumptionProductionToggle';
import { weatherButtonMap } from 'features/map-controls/MapControls';
import SpatialAggregatesToggle from 'features/map-controls/SpatialAggregatesToggle';
import { useAtom } from 'jotai';
import { MoonLoader } from 'react-spinners';
import { useTranslation } from 'translation/translation';
import { TimeAverages, ToggleOptions } from 'utils/constants';
import {
  colorblindModeAtom,
  selectedDatetimeIndexAtom,
  timeAverageAtom,
} from 'utils/state/atoms';
import { isSettingsModalOpenAtom } from './modalAtoms';
import ThemeSelector from 'features/map-controls/ThemeSelector';
import { LanguageSelector } from 'features/map-controls/LanguageSelector';
import { HiOutlineEyeOff } from 'react-icons/hi';

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
        className={isEnabled ? 'bg-brand-green text-white dark:bg-brand-green' : ''}
        disabled={!allowed}
        icon={
          isLoadingLayer ? (
            <MoonLoader size={14} color="white" className="mr-1" />
          ) : (
            <Icon size={weatherButtonMap[type].iconSize} />
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
  const [timeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [isColorblindModeEnabled, setIsColorblindModeEnabled] =
    useAtom(colorblindModeAtom);

  // We are currently only supporting and fetching weather data for the latest hourly value
  const areWeatherLayersAllowed =
    selectedDatetime.index === 24 && timeAverage === TimeAverages.HOURLY;

  const { __ } = useTranslation();
  return (
    <div className="flex flex-col items-center space-y-4">
      <ConsumptionProductionToggle />
      <SpatialAggregatesToggle />
      <LanguageSelector isMobile />
      <WeatherToggleButton allowed={areWeatherLayersAllowed} type="wind" />
      <WeatherToggleButton allowed={areWeatherLayersAllowed} type="solar" />
      <Button
        className={
          isColorblindModeEnabled ? 'bg-brand-green text-white dark:bg-brand-green' : ''
        }
        onClick={() => setIsColorblindModeEnabled(!isColorblindModeEnabled)}
        icon={<HiOutlineEyeOff size={21} />}
      >
        {__('legends.colorblindmode')}
      </Button>
      <ThemeSelector isMobile />
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
