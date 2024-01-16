import Badge from 'components/Badge';
import { useState } from 'react';
import { HiChevronDown, HiChevronUp } from 'react-icons/hi2';
import { EstimationProps } from 'types';

// TODO: This function is temporary until we have the text in the json files
function GetTitle(estimationData: EstimationProps) {
  return 'Data is estimated';
}

// TODO: This function is temporary until we have the text in the json files
function GetPillText(estimationData: EstimationProps) {
  if (estimationData.isOutage) {
    return 'Unavailable';
  }
  return 'Delayed';
}

// TODO: This function is temporary until we have the text in the json files
function GetBodyText(estimationData: EstimationProps) {
  if (estimationData.isOutage) {
    return 'The data provider (EIA) for this zone is currently down. The displayed values are estimates and will be replaced by measured data once available again. We expect to resolve this issues shortly!';
  }
  return 'The data for this hour has not yet been reported. The displayed values are estimates and will be replaced with measured data once available.';
}

export default function EstimationCard({
  estimationData,
}: {
  estimationData: EstimationProps;
}) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const handleToggleCollapse = () => {
    setIsCollapsed((previous) => !previous);
  };
  const bgColorClasses = estimationData.isOutage
    ? 'bg-amber-700/20 dark:bg-amber-500/20'
    : 'bg-neutral-100 dark:bg-gray-800';
  const textColorTitle = 'text-amber-700 dark:text-amber-500';
  const textColorBody = 'text-neutral-600 dark:text-neutral-400';
  const textColorLink = 'text-black dark:text-white';
  const borderColor = 'border-neutral-200 dark:border-gray-700';

  const pillType = estimationData.isOutage
    ? 'outage'
    : (estimationData.isAggregated
    ? 'aggregated'
    : 'estimated');

  return (
    <div
      className={`w-full rounded-lg px-3 py-2.5 ${
        isCollapsed ? 'h-[46px]' : 'h-fit'
      } ${bgColorClasses} border ${borderColor} mb-4 gap-2 transition-all`}
    >
      <div className="flex flex-col">
        <button onClick={handleToggleCollapse}>
          <div className="flex flex-row justify-between pb-2">
            <div className="flex flex-row gap-2">
              <div className={`flex items-center justify-center`}>
                <div className=" h-[16px] w-[16px] bg-[url('/images/estimated_light.svg')] bg-center dark:bg-[url('/images/estimated_dark.svg')]" />
              </div>
              <h2
                className={`truncate text-sm font-semibold ${textColorTitle} self-center`}
              >
                {GetTitle(estimationData)}
              </h2>
            </div>
            <div className="flex flex-row gap-2 ">
              <Badge type={pillType}>{GetPillText(estimationData)}</Badge>
              <div className="text-lg">
                {isCollapsed ? <HiChevronUp /> : <HiChevronDown />}
              </div>
            </div>
          </div>
        </button>
        {!isCollapsed && (
          <div className="gap-2">
            <div className={`text-sm font-normal ${textColorBody}`}>
              {GetBodyText(estimationData)}
            </div>
            <div className="">
              <a
                href="https://www.electricitymaps.com/methodology"
                target="_blank"
                rel="noreferrer"
                className={`text-sm font-semibold underline ${textColorLink}`}
              >
                <span className="underline">Read about our estimation models</span>
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
