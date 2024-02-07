import React from 'react';
import { twMerge } from 'tailwind-merge';

// This value is selected based on appropriate size given most labels in most languages.
const BUTTON_MIN_WIDTH_CLASS = 'min-w-[232px]';

// TODO: This should extend either HTMLButtonElement or HTMLAnchorElement, but I could not get it
// to properly select the correct one based on given props.
interface ButtonProps {
  icon?: React.ReactNode;
  children?: React.ReactNode;
  disabled?: boolean;
  background?: string;
  textColor?: string;
  href?: string;
  className?: string;
  onClick?: () => void;
}

export function Button({
  icon,
  children,
  disabled,
  background,
  textColor,
  href,
  className,
  onClick,
}: ButtonProps) {
  const renderAsLink = Boolean(href);
  const As = renderAsLink ? 'a' : 'button';
  const type = renderAsLink ? undefined : 'button';
  const isIconOnly = !children && Boolean(icon);

  return (
    <As
      className={twMerge(
        `mx-2 my-3 flex min-h-[45px] w-fit items-center justify-center gap-x-2 rounded-full bg-white px-2 py-3 text-md font-bold shadow-[0px_0px_13px_rgb(0_0_0/12%)] transition duration-200 hover:shadow-[0px_0px_23px_rgb(0_0_0/20%)] dark:bg-gray-600 dark:hover:shadow-[0px_0px_23px_rgb(0_0_0/50%)]`,
        !isIconOnly && BUTTON_MIN_WIDTH_CLASS,
        `${disabled ? 'opacity-60 hover:shadow-[0px_0px_13px_rgb(0_0_0/12%)]' : ''}`,
        className
      )}
      translate="no"
      disabled={disabled}
      style={{ color: textColor, background: background }}
      href={href}
      type={type}
      onClick={onClick}
    >
      {icon}
      {children}
    </As>
  );
}
