import React from 'react';

interface ButtonProps {
  icon?: React.ReactNode;
  children?: React.ReactNode;
  disabled?: boolean;
  size: 'sm' | 'lg' | 'xl';
  variant: 'primary' | 'secondary' | 'secondary-elevated' | 'tertiary' | 'link';
  href?: string;
  backgroundClasses?: string;
  forgroundClasses?: string;
  focusOutlineColor?: string;
  onClick?: () => void;
}

export function RoundedButton({
  icon,
  children,
  disabled,
  href,
  backgroundClasses, // backgroundColor, borderColor, margin, etc.
  forgroundClasses, // textColor, etc.
  focusOutlineColor,
  size,
  variant,
  onClick,
}: ButtonProps) {
  const renderAsLink = Boolean(href);
  const As = renderAsLink ? 'a' : 'button';
  const type = renderAsLink ? undefined : 'button';

  return (
    <div
      className={`m-2 items-center justify-center rounded-full ${getBackground(
        variant,
        disabled
      )} ${backgroundClasses}`}
    >
      <As
        className={`flex h-full w-full flex-row items-center justify-center rounded-full text-sm font-semibold disabled:text-neutral-400
        disabled:hover:bg-inherit disabled:dark:text-gray-500
       ${getSize(size, variant)} ${getFocusedClassesFromVariant(
          focusOutlineColor
        )} ${getForeground(variant)} ${getHover(variant)} ${forgroundClasses}`}
        disabled={disabled}
        href={href}
        type={type}
        onClick={onClick}
      >
        {icon}
        {children}
      </As>
    </div>
  );
}

function getHover(variant: string) {
  switch (variant) {
    case 'primary': {
      return 'hover:bg-black/20';
    }
    default: {
      return 'hover:bg-neutral-400/10';
    }
  }
}

function getBackground(variant: string, disabled: boolean | undefined) {
  switch (variant) {
    case 'primary': {
      if (disabled) {
        return 'bg-zinc-50 dark:bg-gray-800 border border-1 border-neutral-200 dark:border-gray-700';
      }
      return 'bg-em-green';
    }
    case 'secondary': {
      return 'border border-1 dark:border-gray-700 border-neutral-200 bg-inherit';
    }
    case 'secondary-elevated': {
      return 'border border-1 dark:border-gray-700 border-neutral-200 bg-neutral-100 dark:bg-gray-800';
    }
    default: {
      return 'bg-inherit';
    }
  }
}

function getFocusedClassesFromVariant(focusOutlineColor: string | undefined) {
  const outline = 'focus:outline focus:outline-2 outline-offset-2 focus:bg-inherit ';
  return focusOutlineColor ? outline + focusOutlineColor : outline + 'focus:outline-em-green';
}

function getForeground(variant: string) {
  switch (variant) {
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

function getSize(size: string, variant: string) {
  switch (size) {
    case 'sm': {
      return variant == 'link'
        ? 'min-w-7 px-3 py-2 gap-x-1'
        : 'min-w-7 px-2.5 py-1 gap-x-1';
    }
    case 'lg': {
      return variant == 'link'
        ? 'min-w-7 px-3 py-2 gap-x-2'
        : 'min-w-11 px-[18px] py-3 gap-x-1.5';
    }
    case 'xl': {
      return variant == 'link'
        ? 'min-w-7 px-3.5 py-2.5 gap-x-2'
        : 'min-w-14 px-[22px] py-4 gap-x-1.5';
    }
    default: {
      return '';
    }
  }
}
