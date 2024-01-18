import { FiAlertTriangle } from 'react-icons/fi';

type BadgeProps = {
  children: string;
  type: string;
};

export default function Badge({ children, type }: BadgeProps) {
  // set background and text color classes depending on type
  const bgColorClasses =
    type == 'estimated'
      ? 'bg-neutral-200 dark:bg-gray-700'
      : 'bg-amber-700/20 dark:bg-amber-500/20';
  const textColorClasses =
    type == 'estimated'
      ? 'text-black dark:text-white'
      : 'text-amber-700 dark:text-amber-500';

  return (
    <span
      className={`flex flex-row gap-1 rounded-full px-2 py-1 text-[10px] font-semibold ${bgColorClasses} ${textColorClasses}`}
    >
      {type == 'outage' && <FiAlertTriangle className="text-[14px]" />}
      {type == 'aggregated_estimated' && (
        <div className=" h-[16px] w-[16px] bg-[url('/images/estimated_light.svg')] bg-center dark:bg-[url('/images/estimated_dark.svg')]" />
      )}
      {children}
    </span>
  );
}
