import type { Meta, StoryObj } from '@storybook/react';
import { useEffect, useState } from 'react';

import RangeSlider, { RangeSliderProps } from './RangeSlider';

const meta: Meta<typeof RangeSlider> = {
  title: 'basics/RangeSlider',
  component: RangeSlider,
};

export default meta;

function SliderWithControls(arguments_: RangeSliderProps) {
  const [value, setValue] = useState<number[]>(arguments_.value);

  const handleOnSelectedIndexChange = (selectedIndex: number[]) => {
    setValue(selectedIndex);
  };

  useEffect(() => {
    setValue(arguments_.value);
  }, [arguments_.value]);

  return (
    <RangeSlider {...arguments_} value={value} onChange={handleOnSelectedIndexChange} />
  );
}

export const Default = SliderWithControls.bind({}) as StoryObj;
Default.args = {
  value: [0, 10],
};

export const WithCustomStepComponent = SliderWithControls.bind({}) as StoryObj;
WithCustomStepComponent.args = {
  value: [0, 20],
  step: 20,
  trackComponent: (
    <div className="h-2 w-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>
  ),
};

export const WithTrackComponent = SliderWithControls.bind({}) as StoryObj;
WithTrackComponent.args = {
  value: [0, 20],
  trackComponent: (
    <div className="h-2 w-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>
  ),
};
