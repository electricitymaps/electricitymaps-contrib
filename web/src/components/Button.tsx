import React from 'react';
import { twMerge } from 'tailwind-merge';

type SizeOptions = 'sm' | 'md' | 'lg';

type ButtonTypes = 'primary' | 'secondary' | 'tertiary' | 'link';

export interface ButtonProps {
  icon?: React.ReactNode;
  children?: React.ReactNode;
  isDisabled?: boolean;
  size?: SizeOptions;
  shouldShrink?: boolean;
  type?: ButtonTypes;
  href?: string;
  backgroundClasses?: string;
  foregroundClasses?: string;
  asDiv?: boolean;
  onClick?: () => void;
  dataTestId?: string;
}

export function Button({
  icon,
  children,
  isDisabled,
  href,
  backgroundClasses, // backgroundColor, borderColor, margin, etc.
  foregroundClasses, // textColor, etc.
  size = 'lg',
  shouldShrink = false,
  type = 'primary',
  asDiv, // If true, renders a div instead of a button to avoid nested buttons in components like ToastPrimitive.Action
  onClick,
  dataTestId,
}: ButtonProps) {
  const renderAsLink = Boolean(href);
  const As = getComponentType(renderAsLink, asDiv);
  const componentType = renderAsLink ? undefined : 'button';
  const isIconOnly = !children && Boolean(icon);
  return (
    <div
      className={twMerge(
        `items-center justify-center rounded-full ${getBackground(type, isDisabled)}`,
        backgroundClasses,
        shouldShrink ? 'w-fit' : ''
      )}
    >
      <As
        className={twMerge(
          `flex h-full w-full select-none flex-row items-center justify-center rounded-full text-sm font-semibold
        focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-green disabled:text-neutral-400
        disabled:hover:bg-inherit disabled:dark:text-neutral-500 ${getSize(
          size,
          type,
          isIconOnly
        )}
        ${getForeground(type)} ${getHover(type)}`,
          foregroundClasses
        )}
        disabled={isDisabled}
        href={href}
        type={componentType}
        onClick={onClick}
        target="_blank"
        // Used to prevent browser translation crashes on edge, see #6809
        translate="no"
        data-testid={dataTestId}
      >
        {icon}
        {children}
      </As>
    </div>
  );
}

function getComponentType(renderAsLink: boolean, asDiv?: boolean) {
  if (renderAsLink) {
    return 'a';
  }
  if (asDiv) {
    return 'div';
  }

  return 'button';
}

function getHover(type: ButtonTypes) {
  switch (type) {
    case 'primary': {
      return 'hover:bg-black/20';
    }
    default: {
      return 'hover:bg-neutral-400/10';
    }
  }
}

function getBackground(type: ButtonTypes, disabled: boolean | undefined) {
  switch (type) {
    case 'primary': {
      if (disabled) {
        return 'bg-zinc-50 dark:bg-neutral-800 outline outline-1 outline-neutral-200 dark:outline-neutral-700';
      }
      return 'bg-brand-green';
    }
    case 'secondary': {
      return 'outline outline-1 dark:outline-neutral-700 outline-neutral-200 bg-white dark:bg-neutral-900';
    }
    default: {
      return 'bg-inherit';
    }
  }
}

function getForeground(type: ButtonTypes) {
  switch (type) {
    case 'primary': {
      return 'text-white';
    }
    case 'link': {
      return 'text-emerald-800 dark:text-emerald-500';
    }
    default: {
      return 'text-black dark:text-white';
    }
  }
}

function getSize(size: SizeOptions, type: ButtonTypes, isIconOnly: boolean) {
  if (isIconOnly) {
    switch (size) {
      case 'sm': {
        return 'min-w-7 min-h-7';
      }
      case 'md': {
        return 'min-w-9 min-h-9';
      }
      case 'lg': {
        return 'min-w-11 min-h-11';
      }
    }
  }

  switch (size) {
    case 'sm': {
      return 'min-w-6 min-h-6 px-2 py-1 gap-x-1';
    }
    case 'md': {
      return 'min-w-8 min-h-8 px-4 py-2 gap-x-1.5 text-sm';
    }
    case 'lg': {
      return type == 'link'
        ? 'px-4 py-2 gap-x-2'
        : 'min-w-10 min-h-10 px-6 py-3 gap-x-1.5';
    }
    default: {
      return '';
    }
  }
}
