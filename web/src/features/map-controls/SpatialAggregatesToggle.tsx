import ToggleButton from 'components/ToggleButton';
import { useAtom } from 'jotai';
import { memo, type ReactElement, useCallback } from 'react';
import trackEvent from 'utils/analytics';
import { SpatialAggregate, TrackEvent } from 'utils/constants';
import { spatialAggregateAtom } from 'utils/state/atoms';

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

function SpatialAggregatesToggle(): ReactElement {
  const [currentMode, setCurrentMode] = useAtom(spatialAggregateAtom);
  const onSetCurrentMode = useCallback(
    (option: string) => {
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
    },
    [currentMode, setCurrentMode]
  );

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

export default memo(SpatialAggregatesToggle);
