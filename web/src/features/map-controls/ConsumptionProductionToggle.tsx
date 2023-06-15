import ToggleButton from 'components/ToggleButton';
import { useAtom } from 'jotai';
import type { ReactElement } from 'react';
import trackEvent from 'utils/analytics';
import { Mode } from 'utils/constants';
import { productionConsumptionAtom } from 'utils/state/atoms';

export default function ConsumptionProductionToggle(): ReactElement {
  const options = [
    { value: Mode.PRODUCTION, translationKey: 'tooltips.production' },
    { value: Mode.CONSUMPTION, translationKey: 'tooltips.consumption' },
  ];
  const [currentMode, setCurrentMode] = useAtom(productionConsumptionAtom);
  const onSetCurrentMode = (option: string) => {
    if (option === currentMode) {
      return;
    }
    trackEvent('Production Consumption Clicked', { productionConsumption: option });
    setCurrentMode(currentMode === Mode.PRODUCTION ? Mode.CONSUMPTION : Mode.PRODUCTION);
  };

  return (
    <ToggleButton
      options={options}
      tooltipKey="tooltips.cpinfo"
      selectedOption={currentMode}
      onToggle={onSetCurrentMode}
      transparentBackground
    />
  );
}
