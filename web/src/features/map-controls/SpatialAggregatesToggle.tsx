import ToggleButton from 'components/ToggleButton';
import { useAtom } from 'jotai';
import type { ReactElement } from 'react';
import trackEvent from 'utils/analytics';
import { SpatialAggregate, TrackEvent } from 'utils/constants';
import { spatialAggregateAtom } from 'utils/state/atoms';

export default function SpatialAggregatesToggle(): ReactElement {
  const options = [
    {
      value: SpatialAggregate.COUNTRY,
      translationKey: 'aggregateButtons.country',
      dataTestId: 'country-toggle',
    },
    {
      value: SpatialAggregate.ZONE,
      translationKey: 'aggregateButtons.zone',
      dataTestId: 'zone-toggle',
    },
  ];
  const [currentMode, setCurrentMode] = useAtom(spatialAggregateAtom);
  const onSetCurrentMode = (option: string) => {
    if (
      (option === SpatialAggregate.ZONE && currentMode === SpatialAggregate.ZONE) ||
      (option === SpatialAggregate.COUNTRY && currentMode === SpatialAggregate.COUNTRY)
    ) {
      return;
    }
    trackEvent(TrackEvent.SPATIAL_AGGREGATE_CLICKED, { spatialAggregate: option });
    setCurrentMode(
      currentMode === SpatialAggregate.COUNTRY
        ? SpatialAggregate.ZONE
        : SpatialAggregate.COUNTRY
    );
  };

  return (
    <ToggleButton
      options={options}
      tooltipKey="tooltips.aggregateInfo"
      selectedOption={
        currentMode === SpatialAggregate.ZONE ? options[1].value : options[0].value
      }
      onToggle={onSetCurrentMode}
      transparentBackground
    />
  );
}
