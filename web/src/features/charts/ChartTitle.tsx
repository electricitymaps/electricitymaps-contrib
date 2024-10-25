type Props = {
  titleText?: string;
  unit?: string;
  badge?: React.ReactElement;
  className?: string;
};

export function ChartTitle({ titleText, unit, badge, className }: Props) {
  return (
    <div className="flex flex-col pb-0.5">
      <div className={`flex items-center gap-1.5 pt-4 ${className}`}>
        <h2 className="grow">{titleText}</h2>
        {badge}
      </div>
      {unit && <div className="text-sm dark:text-gray-300">{unit}</div>}
    </div>
  );
}
