import ToggleButton from 'components/ToggleButton';
import { useAtom } from 'jotai';
import { memo, type ReactElement, useCallback } from 'react';
import trackEvent from 'utils/analytics';
import { Mode, TrackEvent } from 'utils/constants';
import { productionConsumptionAtom } from 'utils/state/atoms';

const options = [
  {
    value: Mode.PRODUCTION,
    translationKey: 'tooltips.production',
    dataTestId: 'production-toggle',
  },
  {
    value: Mode.CONSUMPTION,
    translationKey: 'tooltips.consumption',
    dataTestId: 'consumption-toggle',
  },
];

function ConsumptionProductionToggle(): ReactElement {
  const [currentMode, setCurrentMode] = useAtom(productionConsumptionAtom);
  const onSetCurrentMode = useCallback(
    (option: string) => {
      if (option === currentMode) {
        return;
      }
      trackEvent(TrackEvent.PRODUCTION_CONSUMPTION_CLICKED, {
        productionConsumption: option,
      });
      setCurrentMode(
        currentMode === Mode.PRODUCTION ? Mode.CONSUMPTION : Mode.PRODUCTION
      );
    },
    [currentMode, setCurrentMode]
  );

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

export default memo(ConsumptionProductionToggle);
