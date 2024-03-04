type BadgeProps = {
  pillText: string;
  type?: string;
  icon?: string;
};

export default function Badge({ pillText, type, icon }: BadgeProps) {
  const classes =
    type == 'warning'
      ? 'bg-amber-700/10 dark:bg-amber-500/10 text-amber-700 dark:text-amber-500'
      : 'bg-neutral-200 dark:bg-gray-700 text-black dark:text-white';

  return (
    <span
      className={`ml-2 flex h-[22px] flex-row gap-1 whitespace-nowrap rounded-full px-2 py-1 text-[10px] font-semibold ${classes}`}
      data-test-id="badge"
    >
      {icon != undefined && <div className={`${icon}`} />}
      {pillText}
    </span>
  );
}
