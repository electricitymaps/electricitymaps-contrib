import type { Meta, StoryObj } from '@storybook/react';

import { useEffect, useState } from 'react';
import {
  TimeSliderBasic,
  TimeSliderProps,
  getThumbIcon,
  getTrackBackground,
} from './TimeSlider';

const MULTI_NIGHT_GRADIENT =
  'linear-gradient(90deg,rgb(243 244 246) 0%, rgb(209 213 219 ) 0%, rgb(209 213 219 ) 12.5%, rgb(243 244 246) 12.5%,rgb(243 244 246) 62.5%, rgb(209 213 219 ) 62.5%, rgb(209 213 219 ) 100%, rgb(243 244 246) 100%)';

const meta: Meta<typeof TimeSliderBasic> = {
  title: 'basics/TimeSlider',
  component: TimeSliderBasic,
};

export default meta;

function SliderWithControls(
  arguments_: TimeSliderProps & { nightTimeSets?: number[][] }
) {
  const [selectedIndex, setSelectedIndex] = useState(arguments_.selectedIndex);

  const handleOnSelectedIndexChange = (selectedIndex: number) => {
    setSelectedIndex(selectedIndex);
  };

  useEffect(() => {
    setSelectedIndex(arguments_.selectedIndex);
  }, [arguments_.selectedIndex]);

  return (
    <TimeSliderBasic
      {...arguments_}
      thumbIcon={getThumbIcon(selectedIndex, arguments_.nightTimeSets)}
      trackBackground={getTrackBackground(
        false,
        arguments_.numberOfEntries,
        arguments_.nightTimeSets
      )}
      selectedIndex={selectedIndex}
      onChange={handleOnSelectedIndexChange}
    />
  );
}

export const Default = SliderWithControls.bind({}) as StoryObj;
Default.args = {
  numberOfEntries: 10,
  selectedIndex: 5,
  nightTimeSets: undefined,
};

export const WithNightTimes = SliderWithControls.bind({}) as StoryObj;
WithNightTimes.args = {
  numberOfEntries: 10,
  selectedIndex: 3,
  trackBackground: MULTI_NIGHT_GRADIENT,
  nightTimeSets: [
    [2, 4],
    [8, 10],
  ],
};
