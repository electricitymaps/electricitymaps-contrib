import * as Popover from '@radix-ui/react-popover';
import { useAtom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { X } from 'lucide-react';

export const POPOVER_ID = 'historical-storytelling-popover';
const popoverDismissed = `${POPOVER_ID}-dismissed`;

export const newFeatureDismissedAtom = atomWithStorage(
  popoverDismissed,
  Boolean(localStorage.getItem(popoverDismissed) ?? false)
);

interface NewFeaturePopoverProps {
  children: React.ReactNode;
  content: string | React.ReactNode;
  side?: 'top' | 'bottom' | 'left' | 'right';
  sideOffset?: number;
  isOpenByDefault?: boolean;
  portal?: boolean;
  onDismiss?: () => void;
}

export function NewFeaturePopover({
  children,
  content,
  side = 'left',
  sideOffset = 6,
  portal = false,
  isOpenByDefault,
}: NewFeaturePopoverProps) {
  const [isDismissed, setIsDismissed] = useAtom(newFeatureDismissedAtom);
  const onDismiss = () => setIsDismissed(true);

  if (!content) {
    return children;
  }

  const inner = (
    <Popover.Content
      hideWhenDetached
      className="z-[51] mx-2.5 flex h-auto max-w-[min(calc(100vw-20px),_400px)] rounded-2xl bg-brand-green p-4 text-center text-sm text-white shadow-md dark:bg-brand-green-dark"
      sideOffset={sideOffset}
      side={side}
    >
      {content}
      <Popover.Close
        data-test-id="dismiss"
        onClick={onDismiss}
        className="self-start text-white"
      >
        <X size={16} />
      </Popover.Close>
      <Popover.Arrow className="fill-brand-green" />
    </Popover.Content>
  );

  return (
    <Popover.Root open={isOpenByDefault && !isDismissed}>
      <Popover.Anchor>{children}</Popover.Anchor>
      {portal ? <Popover.Portal>{inner}</Popover.Portal> : inner}
    </Popover.Root>
  );
}
