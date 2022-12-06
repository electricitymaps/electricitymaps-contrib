import MapButton from 'components/MapButton';
import { ReactElement, useState } from 'react';
import { FiWind } from 'react-icons/fi';
import { HiOutlineSun } from 'react-icons/hi';
import { HiLanguage } from 'react-icons/hi2';
import { useTranslation } from 'translation/translation';
import ConsumptionProductionToggle from './ConsumptionProductionToggle';
import LanguageSelector from './LanguageSelector';
import SpatialAggregatesToggle from './SpatialAggregatesToggle';
interface MapControlsProperties {}

export default function MapControls(properties: MapControlsProperties): ReactElement {
  const { __ } = useTranslation();
  const [isLanguageSelectorOpen, setIsLanguageSelectorOpen] = useState(false);

  return (
    <div className="z-1000 pointer-events-none  absolute right-3 top-3 flex flex-col items-end">
      <div className="pointer-events-auto mb-16 flex flex-col items-end">
        <ConsumptionProductionToggle />
        <div className="mb-1"></div>
        <SpatialAggregatesToggle />
      </div>
      <MapButton
        icon={<HiLanguage size={21} />}
        tooltipText={__('tooltips.selectLanguage')}
        dataTestId="language-selector-open-button"
        className="mt-5"
        onClick={() => setIsLanguageSelectorOpen(!isLanguageSelectorOpen)}
      />
      {isLanguageSelectorOpen && (
        <LanguageSelector setLanguageSelectorOpen={setIsLanguageSelectorOpen} />
      )}
      <MapButton
        icon={<FiWind size={18} />}
        tooltipText={__('tooltips.wind')}
        dataTestId="wind-layer-button"
        className="mt-2"
        onClick={() => {
          console.log('change the toggle weather');
        }}
      />

      <MapButton
        icon={<HiOutlineSun size={21} />}
        className="mt-2"
        dataTestId="solar-layer-button"
        tooltipText={__('tooltips.solar')}
        onClick={() => {
          console.log('change the toggle solar');
        }}
      />
    </div>
  );
}
