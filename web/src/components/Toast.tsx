import * as ToastPrimitive from '@radix-ui/react-toast';
import { CircleCheck, Info, OctagonX, TriangleAlert, X } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { twMerge } from 'tailwind-merge';

import { Button } from './Button';

export enum ToastType {
  INFO = 'info',
  SUCCESS = 'success',
  WARNING = 'warning',
  DANGER = 'danger',
}

interface ToastProps {
  title?: string;
  description: string;
  isCloseable?: boolean;
  toastAction?: () => void;
  toastClose?: () => void;
  toastActionText?: string;
  toastCloseText?: string;
  duration?: number;
  type?: ToastType;
}

export const ToastTypeTheme = {
  [ToastType.SUCCESS]: {
    Icon: CircleCheck,
    color:
      'text-emerald-800 dark:text-emerald-500 before:bg-emerald-800 dark:before:bg-emerald-500',
  },
  [ToastType.WARNING]: {
    Icon: TriangleAlert,
    color:
      'text-amber-700 dark:text-amber-500 before:bg-amber-700 dark:before:bg-amber-500',
  },
  [ToastType.DANGER]: {
    Icon: OctagonX,
    color: 'text-red-700 dark:text-red-400 before:bg-red-700 dark:before:bg-red-400',
  },
  [ToastType.INFO]: {
    Icon: Info,
    color: 'text-blue-800 dark:text-blue-400 before:bg-blue-800 dark:before:bg-blue-400',
  },
};

export function Toast({
  title,
  description,
  toastAction,
  toastActionText,
  toastClose,
  toastCloseText,
  duration,
  type = ToastType.INFO,
}: ToastProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(true);
  const handleToastAction = () => {
    toastAction?.();
    setOpen(false);
  };

  const handleToastClose = () => {
    toastClose?.();
    setOpen(false);
  };

  const { Icon, color } = ToastTypeTheme[type];

  return (
    <>
      <ToastPrimitive.Root
        data-testid="toast"
        open={open}
        onOpenChange={setOpen}
        duration={duration}
        type="background"
        className={twMerge(
          'fixed left-1/2 top-16 z-50 inline-block flex w-11/12 min-w-96 max-w-full -translate-x-1/2 transform rounded-lg shadow xs:w-max',
          'border border-solid border-neutral-50 bg-white/80 backdrop-blur-sm dark:border-gray-700 dark:bg-gray-700 dark:bg-gray-900',
          "before:content[''] before:absolute before:block before:h-full before:w-1 before:rounded-bl-md before:rounded-tl-md",
          color,
          toastAction ? 'h-[52px]' : 'h-11'
        )}
      >
        <div className="flex w-full items-center p-2">
          <div className="flex items-center gap-2 px-2">
            <Icon className={twMerge(color, 'w-4 min-w-4')} data-testid="toast-icon" />
            <div className="flex flex-col">
              {title && (
                <ToastPrimitive.Title className="text-md font-bold">
                  {title}
                </ToastPrimitive.Title>
              )}
              {description && (
                <ToastPrimitive.Description className="text-sm font-semibold">
                  {description}
                </ToastPrimitive.Description>
              )}
            </div>
          </div>
          <div className="ml-auto flex">
            {toastAction && (
              <ToastPrimitive.Action
                altText="view now"
                className="flex items-center justify-center"
                onClick={handleToastAction}
              >
                <Button size="md" asDiv>
                  {toastActionText}
                </Button>
              </ToastPrimitive.Action>
            )}
            <ToastPrimitive.Close
              className="mx-2 flex items-center justify-center text-black dark:text-white"
              onClick={handleToastClose}
              aria-label={toastCloseText ?? t('misc.dismiss')}
              data-testid="toast-dismiss"
            >
              <X size={16} />
            </ToastPrimitive.Close>
          </div>
        </div>
      </ToastPrimitive.Root>
      <ToastPrimitive.Viewport />
    </>
  );
}
