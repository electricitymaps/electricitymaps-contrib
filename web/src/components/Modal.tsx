import * as Dialog from '@radix-ui/react-dialog';
import { HiXMark } from 'react-icons/hi2';

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
        <Dialog.Overlay className="fixed inset-0 z-20 bg-black/50" />
        <Dialog.Content
          // Avoid close button being auto-focused initially, as pressing space will otherwise close the modal
          onOpenAutoFocus={(event: Event) => event.preventDefault()}
          data-test-id={testId}
          className={`fixed left-[50%] top-[50%] z-40 w-[98vw] max-w-2xl -translate-x-[50%] -translate-y-[50%] rounded-xl bg-white/90 shadow-md backdrop-blur-sm dark:bg-gray-800/90 sm:w-[90vw] ${
            fullWidth ? 'p-0' : 'p-4'
          }`}
        >
          {title && (
            <Dialog.Title className="text-center font-poppins sm:text-lg">
              {title}
            </Dialog.Title>
          )}
          <Dialog.Close
            className="absolute right-2 top-2 rounded-full bg-gray-100 p-1.5 hover:bg-gray-200 dark:bg-gray-900 dark:hover:bg-gray-700"
            aria-label="Close"
            data-test-id="close-modal-button"
          >
            <HiXMark size="18" />
          </Dialog.Close>
          <div className={fullWidth ? 'p-0' : 'px-2 py-3 sm:p-[25px_55px]'}>
            {children}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
