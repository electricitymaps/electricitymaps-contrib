import Badge from 'components/Badge';
import { useState } from 'react';
import { HiChevronDown, HiChevronUp } from 'react-icons/hi2';

type CardProps = {
  cardType?: 'default' | 'warning';
  estimationType: 'ts_avg' | 'data_outage';
};

export default function EstimationCard({
  cardType = 'default',
  estimationType,
}: CardProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const handleToggleCollapse = () => {
    setIsCollapsed((previous) => !previous);
  };
  const bgColorClasses = {
    default: 'bg-neutral-100 dark:bg-gray-800',
    warning: 'bg-amber-700/20 dark:bg-amber-500/20',
  }[cardType];
  const textColorTitle = 'text-amber-700 dark:text-amber-500';
  const textColorBody = 'text-neutral-600 dark:text-neutral-400';
  const textColorLink = 'text-black dark:text-white';
  const borderColor = 'border-neutral-200 dark:border-gray-700';

  const estimationTypes = {
    ts_avg: {
      title: 'Data is estimated',
      pillText: 'Delayed',
      bodyText:
        'The data for this hour has not yet been reported. The displayed values are estimates and will be replaced with measured data once available.',
    },
    data_outage: {
      title: 'Data is estimated',
      pillText: 'Unavailable',
      bodyText:
        'The data provider (EIA) for this zone is currently down. The displayed values are estimates and will be replaced by measured data once available again. We expect to resolve this issues shortly!',
    },
  };
  const { title, pillText, bodyText } = estimationTypes[estimationType];

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
                <div className=" h-[16px] w-[16px] bg-[url('/images/estimated_light.svg')] bg-center dark:bg-[url('/images/estimated_dark.svg')]"></div>
              </div>
              <h2
                className={`truncate text-sm font-semibold ${textColorTitle} self-center`}
              >
                {title}
              </h2>
            </div>
            <div className="flex flex-row gap-2 ">
              <Badge type={cardType}>{pillText}</Badge>
              <div className="text-lg">
                {isCollapsed ? <HiChevronUp /> : <HiChevronDown />}
              </div>
            </div>
          </div>
        </button>
        {!isCollapsed && (
          <div className="gap-2">
            <div className={`text-sm font-normal ${textColorBody}`}>{bodyText}</div>
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
