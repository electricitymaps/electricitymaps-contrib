import ToggleButton from 'components/ToggleButton';
import { useEvents, useTrackEvent } from 'hooks/useTrackEvent';
import { useAtom } from 'jotai';
import { memo, type ReactElement, useCallback } from 'react';
import { SpatialAggregate } from 'utils/constants';
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
  const trackEvent = useTrackEvent();
  const { trackZoneMode } = useEvents(trackEvent);

  const onSetCurrentMode = useCallback(
    (option: SpatialAggregate | '') => {
      if (option === '') {
        return;
      }
      trackZoneMode(option);
      setCurrentMode(option);
    },
    [setCurrentMode, trackZoneMode]
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
