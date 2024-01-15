type BadgeProps = {
  children: string;
  type?: 'default' | 'warning';
  className?: string;
};

export default function Badge({ children, type = 'default', className }: BadgeProps) {
  // set background and text color classes depending on type
  const bgColorClasses = {
    default: 'bg-[#E5E5E5] dark:bg-[#374151]',
    warning: 'bg-yellow-400 dark:bg-yellow-500',
  }[type];
  const textColorClasses = {
    default: 'text-black dark:text-white',
    warning: 'text-yellow-900/95 dark:text-gray-900/95',
  }[type];

  return (
    <span
      className={`rounded-full px-2 py-1 text-[10px] font-semibold ${bgColorClasses} ${textColorClasses} ${className}`}
    >
      {children}
    </span>
  );
}
