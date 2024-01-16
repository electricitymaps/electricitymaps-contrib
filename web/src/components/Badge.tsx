import { FiAlertTriangle } from 'react-icons/fi';

type BadgeProps = {
  children: string;
  type?: 'default' | 'warning';
  className?: string;
};

export default function Badge({ children, type = 'default', className }: BadgeProps) {
  // set background and text color classes depending on type
  const bgColorClasses = {
    default: 'bg-[#E5E5E5] dark:bg-[#374151]',
    warning: 'bg-[#B45309]/20 dark:bg-[#F59E0B]/20',
  }[type];
  const textColorClasses = {
    default: 'text-black dark:text-white',
    warning: 'text-[#B45309] dark:text-[#F59E0B]',
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
