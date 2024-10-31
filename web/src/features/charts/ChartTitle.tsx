import { MoreOptionsDropdown, useShowMoreOptions } from 'components/MoreOptionsDropdown';
import { Ellipsis } from 'lucide-react';
import { Charts } from 'utils/constants';

type Props = {
  titleText?: string;
  unit?: string;
  estimationBadge?: React.ReactElement;
  className?: string;
  id?: Charts;
};

export function ChartTitle({ titleText, unit, estimationBadge, className, id }: Props) {
  const showMoreOptions = useShowMoreOptions();
  return (
    <div className="flex flex-col pb-0.5">
      <div className={`flex items-center gap-1.5 pt-4 ${className}`}>
        <h2 id={id} className="grow">
          {titleText}
        </h2>
        {estimationBadge}
        {showMoreOptions && (
          <MoreOptionsDropdown isEstimated={Boolean(estimationBadge)}>
            <Ellipsis />
          </MoreOptionsDropdown>
        )}
      </div>
      {unit && <div className="text-sm dark:text-gray-300">{unit}</div>}
    </div>
  );
}
