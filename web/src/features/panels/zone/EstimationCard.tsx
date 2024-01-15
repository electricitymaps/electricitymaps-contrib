import Badge from 'components/Badge';
import { he } from 'date-fns/locale';
import React, { useState } from 'react';
import { HiChevronDown, HiChevronUp } from 'react-icons/hi2';

type CardProps = {
  cardType?: 'default' | 'warning';
  estimationType: 'ts_avg' | 'data_outage';
};

export function EstimationCard({ cardType = 'default', estimationType }: CardProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const handleToggleCollapse = () => {
    setIsCollapsed((previous) => !previous);
  };
  const bgColorClasses = {
    default: 'bg-[#F5F5F5] dark:bg-[#1F2937]',
    warning: 'bg-[#B45309]/20 dark:bg-[#F59E0B]/20',
  }[cardType];
  const textColorTitle = 'text-[#B45309] dark:text-[#F59E0B]';
  const textColorBody = 'text-[#525252] dark:text-[#A3A3A3]';
  const textColorLink = 'text-[#000000] dark:text-[#FFFFFF]';
  const borderColor = 'border-[#E5E5E5] dark:border-[#374151]';

  const title = {
    ts_avg: 'Data is estimated',
    data_outage: 'Data is estimated',
  }[estimationType];
  const pillText = {
    ts_avg: 'Delayed',
    data_outage: 'Unavailable',
  }[estimationType];
  const bodyText = {
    ts_avg:
      'The data for this hour has not yet been reported. The displayed values are estimates and will be replaced with measured data once available.',
    data_outage:
      'The data provider (EIA) for this zone is currently down. The displayed values are estimates and will be replaced by measured data once available again. We expect to resolve this issues shortly!',
  }[estimationType];

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
                style={{ textDecoration: 'none' }}
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

export default EstimationCard;
