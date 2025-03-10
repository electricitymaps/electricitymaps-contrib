import React from 'react';

export type PillType = 'default' | 'warning' | 'success';

type BadgeProps = {
  pillText: string | JSX.Element;
  type?: PillType;
  icon?: React.ReactElement;
};

export default function Badge({ pillText, type, icon }: BadgeProps) {
  let classes = '';

  switch (type) {
    case 'warning': {
      classes =
        'bg-warning/10 dark:bg-warning-dark/10 text-warning dark:text-warning-dark';
      break;
    }
    case 'success': {
      classes =
        'bg-success/10 dark:bg-success-dark/10 text-success dark:text-success-dark';
      break;
    }
    default: {
      classes = 'bg-neutral-200 dark:bg-gray-700 text-black dark:text-white';
    }
  }

  return (
    <span
      className={`flex h-6 flex-row items-center gap-1 whitespace-nowrap rounded-full px-2 py-1 text-xs font-semibold ${classes}`}
      data-testid="badge"
    >
      {icon}
      {pillText}
    </span>
  );
}
