import * as Popover from '@radix-ui/react-popover';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useAtom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { X } from 'lucide-react';

export const newFeatureDismissedAtom = atomWithStorage(
  'newFeatureDismissed',
  Boolean(localStorage.getItem('newFeatureDismissed') ?? false)
);

interface NewFeaturePopoverProps {
  children: React.ReactNode;
  content: string | React.ReactNode;
  side?: 'top' | 'bottom' | 'left' | 'right';
  sideOffset?: number;
  isOpen?: boolean;
  portal?: boolean;
  onDismiss?: () => void;
}

export function NewFeaturePopover({
  children,
  content,
  side = 'left',
  sideOffset = 6,
  portal = false,
}: NewFeaturePopoverProps) {
  const [isDismissed, setIsDismissed] = useAtom(newFeatureDismissedAtom);
  const isNewFeaturePopoverEnabled = useFeatureFlag('new-feature-popover');
  const onDismiss = () => setIsDismissed(true);
  const shouldDisplayPopover = isNewFeaturePopoverEnabled && !isDismissed;

  if (!content) {
    return children;
  }

  const inner = (
    <Popover.Content
      collisionPadding={10}
      avoidCollisions
      className="z-[51] flex h-auto max-w-[350px] rounded-2xl bg-brand-green p-4 text-center text-sm text-white shadow-md dark:bg-brand-green-dark sm:max-w-sm"
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
    <Popover.Root open={shouldDisplayPopover}>
      <Popover.Anchor>{children}</Popover.Anchor>
      {portal ? <Popover.Portal>{inner}</Popover.Portal> : inner}
    </Popover.Root>
  );
}
