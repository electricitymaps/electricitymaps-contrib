import * as SliderPrimitive from '@radix-ui/react-slider';

interface TimeSliderProps {
  onChange: (datetimeIndex: number) => void;
  numberOfEntries: number;
  selectedIndex?: number;
}

function TimeSlider({ onChange, numberOfEntries, selectedIndex }: TimeSliderProps) {
  return (
    <SliderPrimitive.Root
      defaultValue={[0]}
      max={numberOfEntries}
      step={1}
      value={selectedIndex && selectedIndex > 0 ? [selectedIndex] : [0]}
      onValueChange={(value) => onChange(value[0])}
      aria-label="value"
      className="relative mb-2 flex h-5 w-full touch-none items-center"
    >
      <SliderPrimitive.Track className="relative h-2.5 w-full grow rounded-sm bg-gray-100 dark:bg-gray-700">
        <SliderPrimitive.Range />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb
        data-test-id="time-slider-input"
        className={`block h-6 w-6 rounded-full bg-white bg-[url("/images/slider-thumb.svg")]
          bg-center bg-no-repeat shadow-3xl focus:outline-none
          focus-visible:ring focus-visible:ring-brand-green/10
          focus-visible:ring-opacity-75 dark:bg-gray-400 dark:focus-visible:ring-white/70`}
      ></SliderPrimitive.Thumb>
    </SliderPrimitive.Root>
  );
}

export default TimeSlider;
