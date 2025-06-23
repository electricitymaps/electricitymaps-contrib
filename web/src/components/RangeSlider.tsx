import * as SliderPrimitive from '@radix-ui/react-slider';
import * as Tooltip from '@radix-ui/react-tooltip';
import { Menu } from 'lucide-react';
import { memo, type ReactElement } from 'react';

import LabelTooltip from './tooltips/LabelTooltip';
import TooltipWrapper from './tooltips/TooltipWrapper';

export interface RangeSliderProps {
  onChange: (values: number[]) => void;
  defaultValue: number[];
  maxValue: number;
  step: number;
  value: number[];
  trackComponent?: string | ReactElement;
}

function RangeSlider({
  onChange,
  defaultValue,
  maxValue,
  step,
  value,
  trackComponent,
}: RangeSliderProps): ReactElement {
  return (
    <Tooltip.Provider delayDuration={0}>
      <SliderPrimitive.Root
        defaultValue={defaultValue}
        max={maxValue}
        step={step}
        value={value}
        onValueChange={onChange}
        aria-label="select range"
        className="relative flex h-8 w-full touch-none hover:cursor-pointer"
        minStepsBetweenThumbs={1}
      >
        <SliderPrimitive.Track className="pointer-events-none relative h-2.5 w-full rounded-md ">
          {trackComponent ?? (
            <div className="h-2 w-full bg-neutral-100 dark:bg-neutral-600"></div>
          )}
        </SliderPrimitive.Track>

        <TooltipWrapper
          tooltipContent={<LabelTooltip className={'text-xs'}>{value[0]}</LabelTooltip>}
          side="top"
          sideOffset={4}
        >
          <SliderPrimitive.Thumb
            data-testid="range-slider-input-1"
            className="-ml-2.5 -mt-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-white p-1 outline
           outline-1 outline-neutral-200 hover:outline-2 focus-visible:outline-2 focus-visible:outline-brand-green dark:bg-neutral-900 dark:outline-neutral-700 dark:focus-visible:outline-brand-green"
          >
            <Menu className="rotate-90" size={12} />
          </SliderPrimitive.Thumb>
        </TooltipWrapper>

        <TooltipWrapper
          tooltipContent={<LabelTooltip className={'text-xs'}>{value[1]}</LabelTooltip>}
          side="top"
          sideOffset={4}
        >
          <SliderPrimitive.Thumb
            data-testid="range-slider-input-2"
            className="-mr-2.5 -mt-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-white p-1 outline
           outline-1 outline-neutral-200 hover:outline-2 focus-visible:outline-2 focus-visible:outline-brand-green dark:bg-neutral-900 dark:outline-neutral-700 dark:focus-visible:outline-brand-green"
          >
            <Menu className="rotate-90" size={12} />
          </SliderPrimitive.Thumb>
        </TooltipWrapper>
      </SliderPrimitive.Root>
    </Tooltip.Provider>
  );
}

export default memo(RangeSlider);
