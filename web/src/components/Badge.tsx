type BadgeProps = {
  children: string;
  type?: 'default' | 'warning';
  className?: string;
};

export default function Badge({ children, type = 'default', className }: BadgeProps) {
  // set background and text color classes depending on type
  const bgColorClasses = {
    default: 'bg-gray-300 dark:bg-gray-500/40',
    warning: 'bg-yellow-400 dark:bg-yellow-500',
  }[type];
  const textColorClasses = {
    default: 'text-gray-800/90 dark:text-gray-200/90',
    warning: 'text-yellow-900/95 dark:text-gray-900/95',
  }[type];

  return (
    <span
      className={`rounded-full px-2 py-[1px] text-sm font-medium ${bgColorClasses} ${textColorClasses} ${className}`}
    >
      {children}
    </span>
  );
}
