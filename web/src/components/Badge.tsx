import { FiAlertTriangle } from 'react-icons/fi';

type BadgeProps = {
  children: string;
  type?: 'default' | 'warning';
  className?: string;
};

export default function Badge({ children, type = 'default', className }: BadgeProps) {
  // set background and text color classes depending on type
  const bgColorClasses = {
    default: 'bg-neutral-200 dark:bg-gray-700',
    warning: 'bg-amber-700/20 dark:bg-amber-500/20',
  }[type];
  const textColorClasses = {
    default: 'text-black dark:text-white',
    warning: 'text-amber-700 dark:text-amber-500',
  }[type];

  return (
    <span
      className={`flex flex-row gap-1 rounded-full px-2 py-1 text-[10px] font-semibold ${bgColorClasses} ${textColorClasses} ${className}`}
    >
      {type == 'warning' && <FiAlertTriangle className="text-[14px]" />}
      {children}
    </span>
  );
}
