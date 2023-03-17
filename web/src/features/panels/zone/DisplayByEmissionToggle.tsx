import ToggleButton from 'components/ToggleButton';
import { useAtom } from 'jotai';
import type { ReactElement } from 'react';
import trackEvent from 'utils/analytics';
import { Mode, LeftPanelToggleOptions } from 'utils/constants';
import { displayByEmissionsAtom, productionConsumptionAtom } from 'utils/state/atoms';

export default function EmissionToggle(): ReactElement {
  const [mixMode] = useAtom(productionConsumptionAtom);
  const [displayByEmissions, setDisplayByEmissions] = useAtom(displayByEmissionsAtom);

  // TODO: perhaps togglebutton should accept boolean values
  const options = [
    {
      value: LeftPanelToggleOptions.ELECTRICITY,
      translationKey:
        mixMode === Mode.PRODUCTION
          ? 'country-panel.electricityproduction'
          : 'country-panel.electricityconsumption',
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
    <div className="px-4 pt-3 xl:px-10">
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
