import * as SliderPrimitive from '@radix-ui/react-slider';
import { scaleLinear } from 'd3-scale';
import { useNightTimes } from 'hooks/nightTimes';
import { useDarkMode } from 'hooks/theme';
import { useAtom } from 'jotai/react';
import { FaArrowsLeftRight, FaMoon, FaSun } from 'react-icons/fa6';
import trackEvent from 'utils/analytics';
import { TimeAverages } from 'utils/constants';
import { useGetZoneFromPath } from 'utils/helpers';
import { timeAverageAtom } from 'utils/state/atoms';

type NightTimeSet = number[];

export interface TimeSliderProps {
  onChange: (datetimeIndex: number) => void;
  numberOfEntries: number;
  selectedIndex?: number;
}

export const COLORS = {
  light: {
    day: 'rgba(229, 231, 235, 0.5)',
    night: 'rgba(75, 85, 99, 0.5)',
  },
  dark: {
    night: 'rgba(75, 85, 99, 0.5)',
    day: 'rgba(156, 163, 175, 0.5)',
  },
};

export const getTrackBackground = (
  isDarkModeEnabled: boolean,
  numberOfEntries: number,
  sets?: NightTimeSet[]
) => {
  const colors = isDarkModeEnabled ? COLORS.dark : COLORS.light;

  if (!sets || sets.length === 0) {
    return colors.day;
  }

  const scale = scaleLinear().domain([0, numberOfEntries]).range([0, 100]);

  const nightTimeSets = sets.map(([start, end]) => [scale(start), scale(end)]);

  const gradientSets = nightTimeSets
    .map(
      ([start, end]) =>
        `${colors.day} ${start}%, ${colors.night} ${start}%, ${colors.night} ${end}%, ${colors.day} ${end}%`
    )
    .join(',\n');

  return `linear-gradient(
    90deg,
    ${gradientSets}
  )`;
};

export const getThumbIcon = (
  selectedIndex?: number,
  sets?: NightTimeSet[]
): React.ReactNode => {
  const size = 14;
  if (selectedIndex === undefined || !sets || sets.length === 0) {
    return <FaArrowsLeftRight size={size} />;
  }
  const isValueAtNight = sets.some(
    ([start, end]) => selectedIndex >= start && selectedIndex <= end && start !== end
  );
  return isValueAtNight ? <FaMoon size={size} /> : <FaSun size={size} />;
};

function trackTimeSliderEvent(selectedIndex: number, timeAverage: TimeAverages) {
  trackEvent('Time Slider Button Interaction', {
    selectedIndex: `${timeAverage}: ${selectedIndex}`,
  });
}

export type TimeSliderBasicProps = TimeSliderProps & {
  trackBackground: string;
  thumbIcon: React.ReactNode;
};
export function TimeSliderBasic({
  onChange,
  numberOfEntries,
  selectedIndex,
  trackBackground,
  thumbIcon,
}: TimeSliderBasicProps) {
  const [timeAverage] = useAtom(timeAverageAtom);
  return (
    <SliderPrimitive.Root
      defaultValue={[0]}
      max={numberOfEntries}
      step={1}
      value={selectedIndex && selectedIndex > 0 ? [selectedIndex] : [0]}
      onValueChange={(value) => {
        onChange(value[0]);
        trackTimeSliderEvent(value[0], timeAverage);
      }}
      aria-label="choose time"
      className="relative my-2 flex h-5 w-full touch-none items-center hover:cursor-pointer"
    >
      <SliderPrimitive.Track
        className="relative h-2.5 w-full grow rounded-full backdrop-blur-sm"
        style={{ background: trackBackground }}
      >
        <SliderPrimitive.Range />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb
        data-test-id="time-slider-input"
        className="gray-200/50 flex h-6 w-6 items-center
          justify-center rounded-full shadow-3xl
          backdrop-blur-sm transition-shadow hover:ring hover:ring-success/10
          hover:ring-opacity-50 focus:outline-none
          focus-visible:ring focus-visible:ring-success/10 focus-visible:ring-opacity-75
          dark:bg-gray-400/50 hover:dark:ring-success-dark/10 dark:focus-visible:ring-success-dark/10"
      >
        {thumbIcon}
      </SliderPrimitive.Thumb>
    </SliderPrimitive.Root>
  );
}

export function TimeSliderWithoutNight(props: TimeSliderProps) {
  const isDarkModeEnabled = useDarkMode();
  const thumbIcon = getThumbIcon();
  const trackBackground = getTrackBackground(isDarkModeEnabled, props.numberOfEntries);
  return (
    <TimeSliderBasic {...props} trackBackground={trackBackground} thumbIcon={thumbIcon} />
  );
}

export function TimeSliderWithNight(props: TimeSliderProps) {
  const nightTimeSets = useNightTimes();
  const isDarkModeEnabled = useDarkMode();

  const thumbIcon = getThumbIcon(props.selectedIndex || 0, nightTimeSets);
  const trackBackground = getTrackBackground(
    isDarkModeEnabled,
    props.numberOfEntries,
    nightTimeSets
  );

  return (
    <TimeSliderBasic {...props} trackBackground={trackBackground} thumbIcon={thumbIcon} />
  );
}

function TimeSlider(props: TimeSliderProps) {
  const zoneId = useGetZoneFromPath();
  const [timeAverage] = useAtom(timeAverageAtom);
  const showNightTime = zoneId && timeAverage === TimeAverages.HOURLY;

  return showNightTime ? (
    <TimeSliderWithNight {...props} />
  ) : (
    <TimeSliderWithoutNight {...props} />
  );
}

export default TimeSlider;
