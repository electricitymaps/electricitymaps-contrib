import ToggleButton from 'components/ToggleButton';
import { useAtom } from 'jotai';
import type { ReactElement } from 'react';
import trackEvent from 'utils/analytics';
import { SpatialAggregate, ToggleOptions } from 'utils/constants';
import { spatialAggregateAtom } from 'utils/state/atoms';

export default function SpatialAggregatesToggle(): ReactElement {
  const options = [
    { value: SpatialAggregate.COUNTRY, translationKey: 'aggregateButtons.country' },
    { value: SpatialAggregate.ZONE, translationKey: 'aggregateButtons.zone' },
  ];
  const [currentMode, setCurrentMode] = useAtom(spatialAggregateAtom);
  const onSetCurrentMode = (option: string) => {
    if (
      (option === SpatialAggregate.ZONE && currentMode === ToggleOptions.OFF) ||
      (option === SpatialAggregate.COUNTRY && currentMode === ToggleOptions.ON)
    ) {
      return;
    }
    trackEvent('Spatial Aggregate Clicked', { spatialAggregate: option });
    setCurrentMode(
      currentMode === ToggleOptions.OFF ? ToggleOptions.ON : ToggleOptions.OFF
    );
  };

  return (
    <ToggleButton
      options={options}
      tooltipKey="tooltips.aggregateInfo"
      selectedOption={
        currentMode === ToggleOptions.OFF ? options[1].value : options[0].value
      }
      onToggle={onSetCurrentMode}
      transparentBackground
    />
  );
}
