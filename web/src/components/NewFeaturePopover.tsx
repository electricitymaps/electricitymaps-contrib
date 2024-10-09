import * as Popover from '@radix-ui/react-popover';
import { X } from 'lucide-react';

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
  isOpen,
  portal = true,
  onDismiss,
}: NewFeaturePopoverProps) {
  if (!content) {
    return children;
  }

  const inner = (
    <Popover.Content
      className="z-[51] flex h-auto max-w-sm rounded-2xl bg-brand-green p-4 text-center text-sm text-white shadow-md dark:bg-brand-green-dark"
      sideOffset={sideOffset}
      side={side}
    >
      {content}
      <Popover.Close onClick={onDismiss} className="self-start text-white">
        <X size={16} />
      </Popover.Close>
      <Popover.Arrow className="fill-brand-green" />
    </Popover.Content>
  );

  return (
    <Popover.Root open={isOpen}>
      <Popover.Anchor>{children}</Popover.Anchor>
      {portal ? <Popover.Portal>{inner}</Popover.Portal> : inner}
    </Popover.Root>
  );
}
