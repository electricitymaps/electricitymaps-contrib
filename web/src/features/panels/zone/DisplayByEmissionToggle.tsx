import ToggleButton from 'components/ToggleButton';
import { useAtom } from 'jotai';
import type { ReactElement } from 'react';
import { Mode } from 'utils/constants';
import { displayByEmissionsAtom, productionConsumptionAtom } from 'utils/state';

export default function EmissionToggle(): ReactElement {
  const [mixMode] = useAtom(productionConsumptionAtom);
  const [displayByEmissions, setDisplayByEmissions] = useAtom(displayByEmissionsAtom);

  // TODO: perhaps togglebutton should accept boolean values
  const options = [
    {
      value: false.toString(),
      translationKey:
        mixMode === Mode.PRODUCTION
          ? 'country-panel.electricityproduction'
          : 'country-panel.electricityconsumption',
    },
    { value: true.toString(), translationKey: 'country-panel.emissions' },
  ];

  const onSetCurrentMode = () => {
    setDisplayByEmissions(!displayByEmissions);
  };

  return (
    <div className="px-2 pt-3 pb-4 xl:px-10">
      <ToggleButton
        options={options}
        selectedOption={displayByEmissions.toString()}
        onToggle={onSetCurrentMode}
      />
    </div>
  );
}
