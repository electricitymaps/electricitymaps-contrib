import ToggleButton from 'components/ToggleButton';
import { useAtom, useAtomValue } from 'jotai';
import type { ReactElement } from 'react';
import trackEvent from 'utils/analytics';
import { LeftPanelToggleOptions } from 'utils/constants';
import { displayByEmissionsAtom, isConsumptionAtom } from 'utils/state/atoms';

export default function EmissionToggle(): ReactElement {
  const isConsumption = useAtomValue(isConsumptionAtom);
  const [displayByEmissions, setDisplayByEmissions] = useAtom(displayByEmissionsAtom);

  // TODO: perhaps togglebutton should accept boolean values
  const options = [
    {
      value: LeftPanelToggleOptions.ELECTRICITY,
      translationKey: isConsumption
        ? 'country-panel.electricityconsumption'
        : 'country-panel.electricityproduction',
    },
    {
      value: LeftPanelToggleOptions.EMISSIONS,
      translationKey: 'country-panel.emissions',
    },
  ];

  const onSetCurrentMode = (option: string) => {
    if (displayByEmissions) {
      trackEvent('PanelProductionButton Clicked');
    } else {
      trackEvent('PanelEmissionButton Clicked');
    }
    if (
      (option === LeftPanelToggleOptions.ELECTRICITY && displayByEmissions) ||
      (option === LeftPanelToggleOptions.EMISSIONS && !displayByEmissions)
    ) {
      setDisplayByEmissions(!displayByEmissions);
    }
  };

  return (
    <div className="my-4">
      <ToggleButton
        options={options}
        selectedOption={
          displayByEmissions
            ? LeftPanelToggleOptions.EMISSIONS
            : LeftPanelToggleOptions.ELECTRICITY
        }
        onToggle={onSetCurrentMode}
      />
    </div>
  );
}
