import React from 'react';

interface ButtonProps {
  icon?: React.ReactNode;
  children?: React.ReactNode;
  disabled?: boolean;
  size: 'sm' | 'lg' | 'xl';
  variant: 'primary' | 'secondary' | 'tertiary' | 'link' | 'custom';
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
  backgroundClasses, // backgroundColor, borderColor, etc.
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
      className={`m-2 items-center justify-center rounded-full ${getBackgroundFromVariant(
        variant,
        disabled
      )} ${backgroundClasses}`}
    >
      <As
        className={`flex h-full w-full flex-row items-center justify-center rounded-full text-sm font-semibold hover:bg-[#9494944D]/30 disabled:hover:bg-inherit
       ${getClassNameFromSize(size, variant)} ${getFocusedClassesFromVariant(
          focusOutlineColor
        )} ${getBorderFromVariant(variant)} ${getDisabledClassesFromVariant(
          variant
        )} ${forgroundClasses}`}
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

function getBorderFromVariant(variant: string) {
  if (variant == 'secondary') {
    return 'border border-gray-300 dark:border-gray-700';
  }
}

function getBackgroundFromVariant(variant: string, disabled: boolean | undefined) {
  if (disabled && variant == 'primary') {
      return 'bg-zinc-50 dark:bg-gray-800';
    }
  switch (variant) {
    case 'primary': {
      return 'bg-em-green text-white';
    }
    case 'secondary': {
      return 'text-black dark:border-gray-700 dark:text-white';
    }
    case 'tertiary': {
      return 'text-black dark:text-white';
    }
    case 'link': {
      return 'text-emerald-800 dark:text-emerald-500';
    }
    default: {
      return '';
    }
  }
}

function getFocusedClassesFromVariant(focusOutlineColor: string | undefined) {
  if (focusOutlineColor) {
    console.log(focusOutlineColor);
    return `focus:outline focus:outline-2 ${focusOutlineColor} outline-offset-2 focus:bg-inherit`;
  } else {
    return 'focus:outline focus:outline-2 focus:outline-em-green outline-offset-2 focus:bg-inherit';
  }
}

function getDisabledClassesFromVariant(variant: string) {
  if (variant == 'link' || variant == 'tertiary') {
    return 'disabled:dark:text-gray-500 disabled:dark:bg-inherit disabled:text-neutral-400';
  }
  return 'disabled:border disabled:border-1 disabled:border-neutral-200 disabled:dark:border-gray-700 disabled:dark:text-gray-500 disabled:text-neutral-400';
}

function getClassNameFromSize(size: string, variant: string) {
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
