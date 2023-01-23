import * as ToastPrimitive from '@radix-ui/react-toast';
import { useState } from 'react';

type Props = {
  title: string;
  description?: string;
  isCloseable?: boolean;
  toastAction?: () => void;
  toastActionText?: string;
};

function Toast(props: Props) {
  const { title, description, toastAction, toastActionText } = props;
  const [open, setOpen] = useState(true);
  const handleToastAction = () => {
    toastAction && toastAction();
    setOpen(false);
  };

  return (
    <>
      <ToastPrimitive.Root
        open={open}
        onOpenChange={setOpen}
        className="radix-state-open:animate-toast-slide-in-right radix-swipe-end:animate-toast-swipe-out radix-state-closed:animate-toast-hide fixed top-16 left-1/2 z-50 w-1/4 self-center rounded-lg  bg-white shadow translate-x-radix-toast-swipe-move-x radix-swipe-cancel:translate-x-0 radix-swipe-cancel:duration-200 radix-swipe-cancel:ease-[ease] dark:bg-gray-900"
      >
        <div className="flex">
          <div className="flex w-0 flex-1 items-start p-4">
            <div className="radix w-full">
              <ToastPrimitive.Title className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {title}
              </ToastPrimitive.Title>
              <ToastPrimitive.Description className="mt-1 text-sm text-gray-700 dark:text-gray-400">
                {description}
              </ToastPrimitive.Description>
            </div>
          </div>
          <div className="flex">
            <div className="flex flex-col space-y-1 px-3 py-2">
              <div className="flex h-0 flex-1">
                {toastAction && (
                  <ToastPrimitive.Action
                    altText="view now"
                    className="flex h-6 w-full items-center justify-center rounded border border-transparent px-3 py-2 text-sm font-medium shadow"
                    onClick={handleToastAction}
                  >
                    {toastActionText}
                  </ToastPrimitive.Action>
                )}
              </div>
              <div className="flex h-0 flex-1 ">
                <ToastPrimitive.Close className="flex h-6 w-full items-center justify-center rounded border border-transparent px-3 py-2 text-sm font-medium shadow">
                  Dismiss
                </ToastPrimitive.Close>
              </div>
            </div>
          </div>
        </div>
      </ToastPrimitive.Root>
      <ToastPrimitive.Viewport />
    </>
  );
}

export default Toast;
