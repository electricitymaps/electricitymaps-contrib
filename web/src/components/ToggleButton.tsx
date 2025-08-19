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
import { memo, ReactElement, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { twMerge } from 'tailwind-merge';

import { GlassBackdrop } from './GlassContainer';

export type ToggleButtonOptions<T extends string> = Array<{
  value: T;
  translationKey: string;
  dataTestId?: string;
}>;
interface ToggleButtonProperties<T extends string> {
  options: ToggleButtonOptions<T>;
  selectedOption: T;
  // radix gives back an empty string if a new value is not selected
  onToggle: (option: T | '') => void;
  tooltipKey?: string;
  transparentBackground?: boolean;
}

function ToggleButton<T extends string>({
  options,
  selectedOption,
  tooltipKey,
  onToggle,
  transparentBackground = true,
}: ToggleButtonProperties<T>): ReactElement {
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
        'relative z-10 flex min-w-fit items-center gap-1 overflow-hidden rounded-full border border-neutral-200 bg-neutral-100 p-1 dark:border-neutral-700/60 dark:bg-neutral-900/80',
        !transparentBackground && 'bg-neutral-200/80'
      )}
    >
      {transparentBackground && <GlassBackdrop />}

      <ToggleGroupRoot
        className={'flex grow flex-row items-center justify-between rounded-full'}
        type="single"
        aria-label="Toggle between modes"
        value={selectedOption}
        onValueChange={onToggle}
      >
        {options.map(({ value, translationKey, dataTestId }, key) => (
          <ToggleGroupItem
            key={`group-item-${key}`}
            value={value}
            data-testid={`toggle-button-${dataTestId ?? value}`}
            className={twMerge(
              'inline-flex h-7 w-full items-center whitespace-nowrap rounded-full bg-neutral-100/0 px-3 text-xs dark:border dark:border-neutral-400/0 dark:bg-transparent',
              value === selectedOption
                ? 'bg-white font-bold text-brand-green shadow-2xl transition duration-500 ease-in-out dark:border dark:border-neutral-400/10 dark:bg-white/20'
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
                  'inline-flex h-7 w-7 select-none items-center justify-center',
                  isToolTipOpen && 'pointer-events-none'
                )}
              >
                <Info className="text-neutral-500 dark:text-neutral-300" />
              </div>
            </TooltipTrigger>
            <TooltipPortal>
              <TooltipContent
                className="relative right-12 z-50 max-w-52 overflow-hidden rounded-xl border bg-zinc-50 p-2 text-center text-xs dark:border-0 dark:bg-neutral-900/80"
                sideOffset={10}
                side="bottom"
                onPointerDownOutside={onToolTipClick}
              >
                <GlassBackdrop />
                <div dangerouslySetInnerHTML={{ __html: t(tooltipKey) }} />
              </TooltipContent>
            </TooltipPortal>
          </TooltipRoot>
        </TooltipProvider>
      )}
    </div>
  );
}

// react and typescript doesn't pass through generics so we need to cast
// https://github.com/DefinitelyTyped/DefinitelyTyped/issues/37087#issuecomment-1765701020
export default memo(ToggleButton) as typeof ToggleButton;
