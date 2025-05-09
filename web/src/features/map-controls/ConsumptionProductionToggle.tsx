import ToggleButton from 'components/ToggleButton';
import { useAtom } from 'jotai';
import { memo, type ReactElement, useCallback } from 'react';
import { Mode } from 'utils/constants';
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

function ConsumptionProductionToggle({
  transparentBackground = true,
}: {
  transparentBackground?: boolean;
}): ReactElement {
  const [currentMode, setCurrentMode] = useAtom(productionConsumptionAtom);
  const onSetCurrentMode = useCallback(
    (option: Mode | '') => {
      if (option === '') {
        return;
      }
      setCurrentMode(option);
    },
    [setCurrentMode]
  );

  return (
    <ToggleButton
      options={options}
      tooltipKey="tooltips.cpinfo"
      selectedOption={currentMode}
      onToggle={onSetCurrentMode}
      transparentBackground={transparentBackground}
    />
  );
}

export default memo(ConsumptionProductionToggle);
