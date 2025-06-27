import * as SliderPrimitive from '@radix-ui/react-slider';
import { scaleLinear } from 'd3-scale';
import { useNightTimes } from 'hooks/nightTimes';
import { useDarkMode } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { ChevronsLeftRight, Moon, Sun } from 'lucide-react';
import { ReactElement } from 'react';
import { useParams } from 'react-router-dom';
import { RouteParameters } from 'types';
import { isFineGranularityAtom } from 'utils/state/atoms';

type NightTimeSet = number[];

export interface TimeSliderProps {
  onChange: (datetimeIndex: number) => void;
  numberOfEntries: number;
  selectedIndex?: number;
}

export enum COLORS {
  LIGHT_DAY = 'rgb(245, 245, 245)', // bg-neutral-100
  LIGHT_NIGHT = 'rgb(209,213,219)', // bg-gray-300
  DARK_DAY = 'rgb(82, 82, 82,.8)', // bg-neutral-600
  DARK_NIGHT = 'rgb(38, 38, 38,.8)', // bg-neutral-800
}

export const getTrackBackground = (
  isDarkModeEnabled: boolean,
  numberOfEntries: number,
  sets?: NightTimeSet[]
) => {
  const colors = isDarkModeEnabled
    ? { day: COLORS.DARK_DAY, night: COLORS.DARK_NIGHT }
    : { day: COLORS.LIGHT_DAY, night: COLORS.LIGHT_NIGHT };

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
): ReactElement => {
  const size = 20;
  if (selectedIndex === undefined || !sets || sets.length === 0) {
    return <ChevronsLeftRight size={size} pointerEvents="none" />;
  }
  const isValueAtNight = sets.some(
    ([start, end]) => selectedIndex >= start && selectedIndex <= end && start !== end
  );
  return isValueAtNight ? (
    <Moon size={size} pointerEvents="none" />
  ) : (
    <Sun size={size} pointerEvents="none" />
  );
};

export type TimeSliderBasicProps = TimeSliderProps & {
  trackBackground: string;
  thumbIcon: ReactElement;
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
      onValueChange={(value) => {
        onChange(value[0]);
      }}
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
        data-testid="time-slider-input"
        className="flex h-7 w-7 items-center justify-center rounded-full bg-white outline
           outline-1 outline-neutral-200 hover:outline-2 focus-visible:outline-2 focus-visible:outline-brand-green dark:bg-neutral-900 dark:outline-neutral-700 dark:focus-visible:outline-brand-green"
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
  const { zoneId } = useParams<RouteParameters>();
  const isFineGranularity = useAtomValue(isFineGranularityAtom);
  const showNightTime = zoneId && isFineGranularity;

  return showNightTime ? (
    <TimeSliderWithNight {...props} />
  ) : (
    <TimeSliderWithoutNight {...props} />
  );
}

export default TimeSlider;
