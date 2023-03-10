import { useTranslation } from 'translation/translation';
import * as Popover from '@radix-ui/react-popover';

interface MapOptionSelectorProps {
  trigger: React.ReactNode;
  children: React.ReactNode;
}
export default function MapOptionSelector({ trigger, children }: MapOptionSelectorProps) {
  const { __ } = useTranslation();

  return (
    <Popover.Root>
      <Popover.Trigger>{trigger}</Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          className="pointer-events-auto max-h-[190px] w-[120px] overflow-auto rounded bg-white dark:bg-gray-900"
          sideOffset={5}
          side="left"
        >
          {children}
          <Popover.Arrow className="fill-white dark:fill-gray-900" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
