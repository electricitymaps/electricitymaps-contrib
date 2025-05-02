import ToggleButton from 'components/ToggleButton';
import { useAtom } from 'jotai';
import { memo, type ReactElement, useCallback } from 'react';
import { trackEvent } from 'utils/analytics';
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

function SpatialAggregatesToggle({
  transparentBackground = false,
}: {
  transparentBackground?: boolean;
}): ReactElement {
  const [currentMode, setCurrentMode] = useAtom(spatialAggregateAtom);
  const onSetCurrentMode = useCallback(
    (option: SpatialAggregate | '') => {
      if (option === '') {
        return;
      }
      trackEvent(TrackEvent.MAP_ZONEMODE_TOGGLED, { type: option });
      setCurrentMode(option);
    },
    [setCurrentMode]
  );

  return (
    <ToggleButton
      options={options}
      selectedOption={currentMode}
      onToggle={onSetCurrentMode}
      transparentBackground={transparentBackground}
    />
  );
}

export default memo(SpatialAggregatesToggle);
