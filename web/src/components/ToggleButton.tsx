import { ReactElement } from 'react';
import * as ToggleGroupPrimitive from '@radix-ui/react-toggle-group';
import * as Tooltip from '@radix-ui/react-tooltip';
import { useTranslation } from '../translation/translation';

interface ToggleButtonProperties {
  options: Array<{ value: string; translationKey: string }>;
  selectedOption: string;
  onToggle: (option: string) => void;
  tooltipKey?: string;
}

export default function ToggleButton({
  options,
  selectedOption,
  tooltipKey,
  onToggle,
}: ToggleButtonProperties): ReactElement {
  const { __ } = useTranslation();
  return (
    <div className="z-10 flex h-9 rounded-full bg-gray-100  px-[5px] py-1  drop-shadow   dark:bg-gray-900">
      <ToggleGroupPrimitive.Root
        className={
          ' flex-start flex h-[26px] flex-grow flex-row items-center justify-between self-center rounded-full    bg-gray-100 shadow-inner   dark:bg-gray-700'
        }
        type="multiple"
        aria-label="Font settings"
      >
        {options.map((option, key) => (
          <ToggleGroupPrimitive.Item
            key={`group-item-${key}`}
            value={option.value}
            onClick={() => onToggle(option.value)}
            className={`
       inline-flex h-[26px] w-full rounded-full px-4 pt-1 text-sm  ${
         option.value === selectedOption
           ? ' box-shadow bg-white  transition duration-500 ease-in-out dark:bg-gray-500'
           : ''
       }`}
          >
            <p className="sans flex-grow select-none  dark:text-white">
              {__(option.translationKey)}
            </p>
          </ToggleGroupPrimitive.Item>
        ))}
      </ToggleGroupPrimitive.Root>
      {tooltipKey && (
        <Tooltip.Provider>
          <Tooltip.Root delayDuration={0}>
            <Tooltip.Trigger asChild>
              <div className="b ml-2 h-6 w-6 select-none justify-center self-center rounded-full bg-white text-center drop-shadow dark:border dark:border-gray-500 dark:bg-gray-900">
                <p>i</p>
              </div>
            </Tooltip.Trigger>
            <Tooltip.Portal>
              <Tooltip.Content
                className="TooltipContent relative right-[48px] max-w-[164px] rounded border bg-gray-100 p-2  text-center text-sm drop-shadow-sm dark:border-0 dark:bg-gray-900"
                sideOffset={10}
                side="bottom"
              >
                <div dangerouslySetInnerHTML={{ __html: __(tooltipKey) }} />
              </Tooltip.Content>
            </Tooltip.Portal>
          </Tooltip.Root>
        </Tooltip.Provider>
      )}
    </div>
  );
}
