import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';

import { GlassBackdrop } from './GlassContainer';

interface ModalProps {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
  title?: string;
  testId?: string;
  children: React.ReactNode;
  fullWidth?: boolean;
}

export default function Modal({
  isOpen,
  setIsOpen,
  title,
  fullWidth,
  testId,
  children,
}: ModalProps) {
  return (
    <Dialog.Root open={isOpen} onOpenChange={setIsOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-30 bg-black/50" />
        <Dialog.Content
          // Avoid close button being auto-focused initially, as pressing space will otherwise close the modal
          onOpenAutoFocus={(event: Event) => event.preventDefault()}
          data-testid={testId}
          className={`fixed left-1/2 top-1/2 z-40 max-h-full w-[98vw] max-w-2xl -translate-x-1/2 -translate-y-1/2 rounded-2xl shadow-md sm:w-[90vw] ${
            fullWidth ? 'p-0' : 'p-4'
          }`}
        >
          <GlassBackdrop className=" overflow-hidden rounded-2xl" />
          {title && (
            <Dialog.Title className="text-center font-poppins text-base sm:text-lg">
              {title}
            </Dialog.Title>
          )}
          <Dialog.Close
            className="absolute right-2 top-2 rounded-full bg-neutral-200 p-1.5 hover:bg-neutral-300 dark:bg-neutral-800 dark:hover:bg-neutral-700"
            aria-label="Close"
            data-testid="close-modal-button"
          >
            <X size="18" />
          </Dialog.Close>
          <div
            className={fullWidth ? 'p-0' : 'px-2 py-3 sm:p-[25px_55px] md:px-2 md:py-4'}
          >
            {children}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
