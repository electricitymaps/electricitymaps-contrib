import * as SliderPrimitive from '@radix-ui/react-slider';

interface TimeSliderProps {
  datetimes: string[];
  onChange: (datetimeIndex: number) => void;
}

function TimeSlider({ datetimes, onChange }: TimeSliderProps) {
  return (
    <SliderPrimitive.Root
      defaultValue={[0]}
      max={datetimes.length - 1}
      step={1}
      onValueChange={(value) => onChange(value[0])}
      aria-label="value"
      className="relative mb-2 flex h-5 w-full touch-none items-center"
    >
      <SliderPrimitive.Track className="relative h-2.5 w-full grow rounded-sm bg-gray-200 dark:bg-gray-800">
        <SliderPrimitive.Range />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb
        className={
          'block h-6 w-6 rounded-full bg-white shadow-xl focus:outline-none focus-visible:ring focus-visible:ring-gray-300 focus-visible:ring-opacity-75 dark:bg-white'
        }
      />
    </SliderPrimitive.Root>
  );
}

export default TimeSlider;
