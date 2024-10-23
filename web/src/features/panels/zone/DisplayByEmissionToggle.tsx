import ToggleButton, { ToggleButtonOptions } from 'components/ToggleButton';
import { useAtom } from 'jotai';
import type { ReactElement } from 'react';
import trackEvent from 'utils/analytics';
import { LeftPanelToggleOptions, TrackEvent } from 'utils/constants';
import { displayByEmissionsAtom } from 'utils/state/atoms';

export default function EmissionToggle(): ReactElement {
  const [displayByEmissions, setDisplayByEmissions] = useAtom(displayByEmissionsAtom);

  // TODO: perhaps togglebutton should accept boolean values
  const options: ToggleButtonOptions = [
    {
      value: LeftPanelToggleOptions.ELECTRICITY,
      translationKey: 'country-panel.electricityconsumption',
    },
    {
      value: LeftPanelToggleOptions.EMISSIONS,
      translationKey: 'country-panel.emissions',
    },
  ];

  const onSetCurrentMode = (option: string) => {
    if (displayByEmissions) {
      trackEvent(TrackEvent.PANEL_PRODUCTION_BUTTON_CLICKED);
    } else {
      trackEvent(TrackEvent.PANEL_EMISSION_BUTTON_CLICKED);
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
