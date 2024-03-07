import React from 'react';

// TODO: Add focus state when it is done
// TODO: Add secondary and tertiary link styles
interface ButtonProps {
  icon?: React.ReactNode;
  children?: React.ReactNode;
  disabled?: boolean;
  size: 'sm' | 'md' | 'lg' | 'xl';
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
      ${className} ${getClassNameFromSize(size)} ${getClassNameFromVariant(variant)}`}
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

function getClassNameFromSize(size: string) {
  switch (size) {
    case 'sm': {
      return 'min-w-7 px-2.5 py-1 gap-x-1';
    }
    case 'md': {
      return 'min-w-10 px-3.5 py-2.5 gap-x-1';
    }
    case 'lg': {
      return 'min-w-11 px-[18px] py-3 gap-x-1.5';
    }
    case 'xl': {
      return 'min-w-14 px-[22px] py-4 gap-x-1.5';
    }
    default: {
      return '';
    }
  }
}

function getClassNameFromVariant(variant: string) {
  switch (variant) {
    case 'primary': {
      return 'bg-em-green-em text-white hover:bg-em-green-s1 active:bg-em-green-em shadow-[0px_0px_13px_rgb(0_0_0/5%)] hover:bg-em-green-s1 focus:shadow-none active:bg-em-green-em disabled:border disabled:bg-background-disabled disabled:text-text-disabled';
    }
    case 'secondary': {
      return '';
    }
    case 'tertiary': {
      return '';
    }
    case 'link': {
      return '';
    }
    default: {
      return '';
    }
  }
}
