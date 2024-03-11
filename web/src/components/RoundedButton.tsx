import React from 'react';

interface ButtonProps {
  icon?: React.ReactNode;
  children?: React.ReactNode;
  disabled?: boolean;
  size: 'sm' | 'lg' | 'xl';
  variant: 'primary' | 'secondary' | 'tertiary' | 'link';
  href?: string;
  className?: string;
  onClick?: () => void;
}

export function RoundedButton({
  icon,
  children,
  disabled,
  href,
  className,
  size,
  variant,
  onClick,
}: ButtonProps) {
  const renderAsLink = Boolean(href);
  const As = renderAsLink ? 'a' : 'button';
  const type = renderAsLink ? undefined : 'button';

  return (
    <As
      className={`flex w-fit flex-row items-center justify-center rounded-full text-sm font-semibold
      ${className} ${getClassesFromVariant(variant, size)} `}
      disabled={disabled}
      href={href}
      type={type}
      onClick={onClick}
    >
      {icon}
      {children}
    </As>
  );
}

function getDefaultClassesFromVariant(variant: string) {
  switch (variant) {
    case 'primary': {
      return 'bg-em-green text-white';
    }
    case 'secondary': {
      return 'outline outline-1 outline-neutral-200 text-black dark:outline-gray-700 dark:bg-gray-900 dark:text-white';
    }
    case 'tertiary': {
      return 'text-black dark:bg-gray-900 dark:text-white';
    }
    case 'link': {
      return 'text-emerald-800 dark:text-emerald-500';
    }
    default: {
      return '';
    }
  }
}

function getHoverClassesFromVariant(variant: string) {
  switch (variant) {
    case 'primary': {
      return 'hover:bg-emerald-900';
    }
    case 'secondary': {
      return 'hover:dark:text-gray-300 hover:bg-zinc-100 hover:text-neutral-600 hover:text-neutral-60 hover:dark:bg-gray-800 hover:dark:text-gray-300';
    }
    case 'tertiary': {
      return 'hover:dark:text-gray-300 hover:bg-zinc-100 hover:text-neutral-600 hover:text-neutral-60 hover:dark:bg-gray-800 hover:dark:text-gray-300';
    }
    case 'link': {
      return 'hover:bg-zinc-100 hover:dark:bg-gray-800';
    }
    default: {
      return '';
    }
  }
}

function getFocusedClassesFromVariant(variant: string) {
  switch (variant) {
    case 'primary': {
      return 'focus:outline focus:outline-2 focus:outline-emerald-500';
    }
    case 'secondary': {
      return 'focus:outline focus:outline-2 focus:outline-em-green focus:dark:bg-gray-900';
    }
    case 'tertiary': {
      return 'focus:outline focus:outline-2 focus:outline-em-green focus:dark:bg-gray-900';
    }
    case 'link': {
      return 'focus:outline focus:outline-2 focus:dark:outline-emerald-500';
    }
    default: {
      return '';
    }
  }
}

function getDisabledClassesFromVariant(variant: string) {
  switch (variant) {
    case 'primary': {
      return 'disabled:outline disabled:outline-1 disabled:dark:bg-gray-900 disabled:text-neutral-400 disabled:dark:outline-gray-700 disabled:outline-neutral-200 disabled:bg-zinc-50';
    }
    case 'secondary': {
      return 'disabled:text-neutral-400 disabled:dark:bg-gray-900 disabled:bg-inherit disabled:dark:text-neutral-400 disabled:dark:outline-gray-700 disabled:outline-neutral-200';
    }
    case 'tertiary': {
      return 'disabled:text-neutral-400 disabled:dark:bg-gray-900 disabled:bg-inherit disabled:dark:text-neutral-400';
    }
    case 'link': {
      return 'disabled:dark:text-gray-500 disabled:dark:bg-inherit disabled:text-neutral-400 disabled:bg-inherit';
    }
    default: {
      return '';
    }
  }
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

function getClassesFromVariant(variant: string, size: string) {
  return `${getDefaultClassesFromVariant(variant)} ${getFocusedClassesFromVariant(
    variant
  )} ${getHoverClassesFromVariant(variant)} ${getDisabledClassesFromVariant(
    variant
  )} ${getClassNameFromSize(size, variant)}`;
}
