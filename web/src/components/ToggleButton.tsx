import {
  Root as ToggleGroupRoot,
  Item as ToggleGroupItem,
} from '@radix-ui/react-toggle-group';
import {
  Provider as TooltipProvider,
  Root as TooltipRoot,
  Trigger as TooltipTrigger,
  Content as TooltipContent,
  Portal as TooltipPortal,
} from '@radix-ui/react-tooltip';
import { ReactElement, useState } from 'react';
import { useTranslation } from '../translation/translation';
import { twMerge } from 'tailwind-merge';

interface ToggleButtonProperties {
  options: Array<{ value: string; translationKey: string }>;
  selectedOption: string;
  onToggle: (option: string) => void;
  tooltipKey?: string;
  fontSize?: string;
}

export default function ToggleButton({
  options,
  selectedOption,
  tooltipKey,
  onToggle,
  fontSize = 'text-sm',
}: ToggleButtonProperties): ReactElement {
  const { __ } = useTranslation();
  const [isToolTipOpen, setIsToolTipOpen] = useState(false);
  const onToolTipClick = () => {
    setIsToolTipOpen(!isToolTipOpen);
  };
  const onKeyPressed = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      onToolTipClick();
    }
  };
  return (
    <div className="z-10 flex h-9 rounded-full bg-zinc-100  px-[5px] py-1  drop-shadow-lg dark:bg-gray-900">
      <ToggleGroupRoot
        className={
          'flex-start flex h-[26px] flex-grow flex-row items-center justify-between self-center rounded-full bg-gray-100 shadow-inner dark:bg-gray-700'
        }
        type="single"
        aria-label="Toggle between modes"
        value={selectedOption}
      >
        {options.map((option, key) => (
          <ToggleGroupItem
            key={`group-item-${key}`}
            value={option.value}
            onClick={() => onToggle(option.value)}
            className={`
       inline-flex h-[26px] w-full  items-center whitespace-nowrap rounded-full px-4 ${fontSize} ${
              option.value === selectedOption
                ? ' bg-white  shadow transition duration-500 ease-in-out dark:bg-gray-500'
                : ''
            }`}
          >
            <p className="sans flex-grow select-none  dark:text-white">
              {__(option.translationKey)}
            </p>
          </ToggleGroupItem>
        ))}
      </ToggleGroupRoot>
      {tooltipKey && (
        <TooltipProvider>
          <TooltipRoot open={isToolTipOpen}>
            <TooltipTrigger asChild>
              <div
                onClick={onToolTipClick}
                onKeyDown={onKeyPressed}
                role="button"
                tabIndex={0}
                className={twMerge(
                  'b ml-2 h-6 w-6 select-none justify-center self-center rounded-full bg-white text-center drop-shadow dark:border dark:border-gray-500 dark:bg-gray-900',
                  isToolTipOpen && 'pointer-events-none'
                )}
              >
                <p>i</p>
              </div>
            </TooltipTrigger>
            <TooltipPortal>
              <TooltipContent
                className="relative right-[48px] z-50 max-w-[164px] rounded border bg-zinc-50 p-2  text-center text-sm drop-shadow-sm dark:border-0 dark:bg-gray-900"
                sideOffset={10}
                side="bottom"
                onPointerDownOutside={onToolTipClick}
              >
                <div dangerouslySetInnerHTML={{ __html: __(tooltipKey) }} />
              </TooltipContent>
            </TooltipPortal>
          </TooltipRoot>
        </TooltipProvider>
      )}
    </div>
  );
}
