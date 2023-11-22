import * as SliderPrimitive from '@radix-ui/react-slider';
import { scaleLinear } from 'd3-scale';
import { useNightTimes } from 'hooks/nightTimes';
import { useDarkMode } from 'hooks/theme';
import { useAtom } from 'jotai/react';
import { TimeAverages } from 'utils/constants';
import { getZoneFromPath } from 'utils/helpers';
import { timeAverageAtom } from 'utils/state/atoms';

type NightTimeSet = number[];
type ThumbIconPath =
  | 'slider-thumb.svg'
  | 'slider-thumb-day.svg'
  | 'slider-thumb-night.svg';

export interface TimeSliderProps {
  onChange: (datetimeIndex: number) => void;
  numberOfEntries: number;
  selectedIndex?: number;
}

export const COLORS = {
  light: {
    day: 'rgb(243,244,246)', // bg-gray-100
    night: 'rgb(209,213,219)', // bg-gray-300
  },
  dark: {
    day: 'rgb(75,85,99)', // bg-gray-600
    night: 'rgb(55,65,81)', // bg-gray-700
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
): ThumbIconPath => {
  if (selectedIndex === undefined || !sets || sets.length === 0) {
    return 'slider-thumb.svg';
  }
  const isValueAtNight = sets.some(
    ([start, end]) => selectedIndex >= start && selectedIndex <= end && start !== end
  );
  return isValueAtNight ? 'slider-thumb-night.svg' : 'slider-thumb-day.svg';
};

export type TimeSliderBasicProps = TimeSliderProps & {
  trackBackground: string;
  thumbIcon: ThumbIconPath;
};
export function TimeSliderBasic({
  onChange,
  numberOfEntries,
  selectedIndex,
  trackBackground,
  thumbIcon,
}: TimeSliderBasicProps) {
  return (
    <SliderPrimitive.Root
      defaultValue={[0]}
      max={numberOfEntries}
      step={1}
      value={selectedIndex && selectedIndex > 0 ? [selectedIndex] : [0]}
      onValueChange={(value) => onChange(value[0])}
      aria-label="choose time"
      className="relative mb-2 flex h-5 w-full touch-none items-center hover:cursor-pointer"
    >
      <SliderPrimitive.Track
        className="relative h-2.5 w-full grow rounded-sm"
        style={{ background: trackBackground }}
      >
        <SliderPrimitive.Range />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb
        data-test-id="time-slider-input"
        className={`block h-6 w-6 rounded-full bg-white bg-center
          bg-no-repeat shadow-3xl transition-shadow hover:ring
          hover:ring-brand-green/10 hover:ring-opacity-75 focus:outline-none focus-visible:ring
          focus-visible:ring-brand-green/10 focus-visible:ring-opacity-75
          dark:bg-gray-400 hover:dark:ring-white/70 dark:focus-visible:ring-white/70`}
        style={{ backgroundImage: `url(/images/${thumbIcon})` }}
      ></SliderPrimitive.Thumb>
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
  const zoneId = getZoneFromPath();
  const [timeAverage] = useAtom(timeAverageAtom);
  const showNightTime = zoneId && timeAverage === TimeAverages.HOURLY;

  return showNightTime ? (
    <TimeSliderWithNight {...props} />
  ) : (
    <TimeSliderWithoutNight {...props} />
  );
}

export default TimeSlider;
