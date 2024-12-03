import {
  Item as ToggleGroupItem,
  Root as ToggleGroupRoot,
} from '@radix-ui/react-toggle-group';
import {
  Content as TooltipContent,
  Portal as TooltipPortal,
  Provider as TooltipProvider,
  Root as TooltipRoot,
  Trigger as TooltipTrigger,
} from '@radix-ui/react-tooltip';
import { Info } from 'lucide-react';
import { ReactElement, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { twMerge } from 'tailwind-merge';

export type ToggleButtonOptions = Array<{
  value: string;
  translationKey: string;
  dataTestId?: string;
}>;
interface ToggleButtonProperties {
  options: ToggleButtonOptions;
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
  const { t } = useTranslation();
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
        'z-10 flex min-w-fit items-center gap-1 rounded-full bg-gray-200/80 p-1 shadow dark:bg-gray-800/80',
        transparentBackground ? 'backdrop-blur-sm' : 'bg-gray-200'
      )}
    >
      <ToggleGroupRoot
        className={'flex grow flex-row items-center justify-between rounded-full'}
        type="single"
        aria-label="Toggle between modes"
        value={selectedOption}
      >
        {options.map(({ value, translationKey, dataTestId }, key) => (
          <ToggleGroupItem
            key={`group-item-${key}`}
            value={value}
            onClick={() => onToggle(value)}
            data-testid={`toggle-button-${dataTestId ?? value}`}
            className={twMerge(
              'inline-flex h-7 w-full items-center whitespace-nowrap rounded-full bg-gray-100/0 px-3 text-xs dark:border dark:border-gray-400/0 dark:bg-transparent',
              value === selectedOption
                ? ' bg-white font-bold text-brand-green shadow transition duration-500 ease-in-out dark:border dark:border-gray-400/10 dark:bg-gray-600'
                : ''
            )}
          >
            <p className="grow select-none text-sm capitalize dark:text-white">
              {t(translationKey)}
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
                  'inline-flex h-7 w-7 select-none items-center justify-center rounded-full bg-white dark:bg-gray-600',
                  isToolTipOpen && 'pointer-events-none'
                )}
              >
                <Info className="text-neutral-500 dark:text-gray-300" />
              </div>
            </TooltipTrigger>
            <TooltipPortal>
              <TooltipContent
                className="relative right-12 z-50 max-w-40 rounded border bg-zinc-50 p-2 text-center text-xs dark:border-0 dark:bg-gray-900"
                sideOffset={10}
                side="bottom"
                onPointerDownOutside={onToolTipClick}
              >
                <div dangerouslySetInnerHTML={{ __html: t(tooltipKey) }} />
              </TooltipContent>
            </TooltipPortal>
          </TooltipRoot>
        </TooltipProvider>
      )}
    </div>
  );
}
