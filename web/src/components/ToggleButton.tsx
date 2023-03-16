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
  transparentBackground?: boolean;
}

export default function ToggleButton({
  options,
  selectedOption,
  tooltipKey,
  onToggle,
  transparentBackground,
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
    <div
      className={twMerge(
        'z-10 flex h-9 rounded-full bg-gray-200/80 px-1  shadow    dark:bg-gray-900',
        transparentBackground ? 'bg-gray-200/80 backdrop-blur-sm' : 'bg-gray-200'
      )}
    >
      <ToggleGroupRoot
        className={
          'flex-start flex flex-grow flex-row items-center justify-between self-center rounded-full dark:bg-gray-700'
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
            className={twMerge(
              'inline-flex h-[29px] w-full items-center whitespace-nowrap rounded-full  bg-gray-100/0 px-4 text-sm',
              option.value === selectedOption
                ? ' bg-white font-bold text-brand-green shadow transition duration-500 ease-in-out dark:bg-gray-500'
                : ''
            )}
          >
            <p className="sans flex-grow select-none capitalize dark:text-white">
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
                  'ml-2 inline-flex h-[29px] w-[29px] select-none justify-center self-center rounded-full bg-white shadow dark:border dark:border-gray-500 dark:bg-gray-900',
                  isToolTipOpen && 'pointer-events-none'
                )}
              >
                <p className="self-center text-sm font-bold">i</p>
              </div>
            </TooltipTrigger>
            <TooltipPortal>
              <TooltipContent
                className="relative right-[48px] z-50 max-w-[164px] rounded border bg-zinc-50 p-2 text-center text-sm dark:border-0 dark:bg-gray-900"
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
