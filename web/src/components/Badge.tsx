type BadgeProps = {
  pillText: string;
  type: string | undefined;
  icon: string | undefined;
};

export default function Badge({ pillText, type, icon }: BadgeProps) {
  const classes =
    type == 'warning'
      ? 'bg-amber-700/20 dark:bg-amber-500/20 text-amber-700 dark:text-amber-500'
      : 'bg-neutral-200 dark:bg-gray-700 text-black dark:text-white';

  return (
    <span
      className={`flex flex-row gap-1 rounded-full px-2 py-1 text-[10px] font-semibold ${classes}`}
    >
      {icon != undefined && <div className={`${icon}`} />}
      {pillText}
    </span>
  );
}
