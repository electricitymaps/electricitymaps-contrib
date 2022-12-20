import MapButton from 'components/MapButton';
import { useAtom } from 'jotai';
import { ReactElement, useState } from 'react';
import { FiWind } from 'react-icons/fi';
import { HiOutlineEyeOff, HiOutlineSun } from 'react-icons/hi';
import { HiLanguage } from 'react-icons/hi2';
import { useTranslation } from 'translation/translation';
import { ToggleOptions } from 'utils/constants';
import { solarLayerAtom, windLayerAtom } from 'utils/state/atoms';
import ConsumptionProductionToggle from './ConsumptionProductionToggle';
import LanguageSelector from './LanguageSelector';
import SpatialAggregatesToggle from './SpatialAggregatesToggle';

export default function MapControls(properties: MapControlsProperties): ReactElement {
  const { __ } = useTranslation();
  const [isLanguageSelectorOpen, setIsLanguageSelectorOpen] = useState(false);
  const [windLayerToggle, setWindLayerToggle] = useAtom(windLayerAtom);
  const [solarLayerToggle, setSolarLayerToggle] = useAtom(solarLayerAtom);

  const onToggleWindLayer = () => {
    setWindLayerToggle(
      windLayerToggle === ToggleOptions.ON ? ToggleOptions.OFF : ToggleOptions.ON
    );
  };

  const onToggleSolarLayer = () => {
    setSolarLayerToggle(
      solarLayerToggle === ToggleOptions.ON ? ToggleOptions.OFF : ToggleOptions.ON
    );
  };

  return (
    <div className="z-1000 pointer-events-none absolute right-3 top-3 hidden flex-col items-end md:flex">
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
        icon={
          <FiWind size={18} color={windLayerToggle === ToggleOptions.ON ? '' : 'gray'} />
        }
        tooltipText={__('tooltips.wind')}
        dataTestId="wind-layer-button"
        className="mt-2"
        onClick={onToggleWindLayer}
      />

      <MapButton
        icon={
          <HiOutlineSun
            size={21}
            color={solarLayerToggle === ToggleOptions.ON ? '' : 'gray'}
          />
        }
        className="mt-2"
        dataTestId="solar-layer-button"
        tooltipText={__('tooltips.solar')}
        onClick={onToggleSolarLayer}
      />

      <MapButton
        icon={<HiOutlineEyeOff size={21} className="opacity-50" />}
        className="mt-2"
        dataTestId="colorblind-layer-button"
        tooltipText={__('legends.colorblindmode')}
        onClick={() => {
          console.log('toggle colorblind mode');
        }}
      />
    </div>
  );
}
