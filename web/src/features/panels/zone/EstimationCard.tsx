import Badge from 'components/Badge';
import { useState } from 'react';
import { HiChevronDown, HiChevronUp } from 'react-icons/hi2';
import { ZoneDetails } from 'types';

// TODO: This function is temporary until we have the text in the json files
function GetTitle(estimationMethod: string | undefined) {
  if (estimationMethod == 'outage') {
    return 'Data is estimated';
  }
  if (estimationMethod == 'aggregated' || estimationMethod == 'aggregated_estimated') {
    return 'Data is aggregated';
  }
  return 'Data is estimated';
}

// TODO: This function is temporary until we have the text in the json files
function GetPillText(estimationMethod: string | undefined) {
  if (estimationMethod == 'outage') {
    return 'Unavailable';
  }
  if (estimationMethod == 'aggregated' || estimationMethod == 'aggregated_estimated') {
    return 'Incl. estimates';
  }
  return 'Delayed';
}

// TODO: This function is temporary until we have the text in the json files
function GetBodyText(estimationMethod: string | undefined) {
  if (estimationMethod == 'outage') {
    return 'The data provider (EIA) for this zone is currently down. The displayed values are estimates and will be replaced by measured data once available again. We expect to resolve this issues shortly!';
  }
  if (estimationMethod == 'aggregated') {
    return 'The data consists of summarised values of hourly recordings throughout the day.';
  }
  if (estimationMethod == 'aggregated_estimated') {
    return 'The data consists of summarised values of hourly recordings throughout the day. Some hourly data is estimated.';
  }
  return 'The data for this hour has not yet been reported. The displayed values are estimates and will be replaced with measured data once available.';
}

export default function EstimationCard({
  cardType,
  estimationMethod,
  outageMessage,
}: {
  cardType: string;
  estimationMethod: string | undefined;
  outageMessage: ZoneDetails['zoneMessage'];
}) {
  if (cardType == 'outage') {
    return <OutageCard outageMessage={outageMessage} />;
  } else if (cardType == 'aggregated_estimated') {
    return <AggregatedEstimatedCard />;
  } else if (cardType == 'aggregated') {
    return <AggregatedCard />;
  } else if (cardType == 'estimated') {
    return <EstimatedCard estimationMethod={estimationMethod} />;
  }
}

function BaseCard({
  estimationMethod,
  outageMessage,
  icon,
  showMethodologyLink,
  showPill,
  cardType,
  bgColorClasses,
  textColorTitle,
}: {
  estimationMethod: string | undefined;
  outageMessage: ZoneDetails['zoneMessage'];
  icon: string;
  showMethodologyLink: boolean;
  showPill: boolean;
  cardType: string;
  bgColorClasses: string;
  textColorTitle: string;
}) {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const handleToggleCollapse = () => {
    setIsCollapsed((previous) => !previous);
  };
  return (
    <div
      className={`w-full rounded-lg px-3 py-2.5 ${
        isCollapsed ? 'h-[46px]' : 'h-fit'
      } ${bgColorClasses} mb-4 gap-2 border border-neutral-200 transition-all dark:border-gray-700`}
    >
      <div className="flex flex-col">
        <button onClick={handleToggleCollapse}>
          <div className="flex flex-row justify-between pb-1.5">
            <div className="flex flex-row gap-2">
              <div className={`flex items-center justify-center`}>
                <div className={`h-[16px] w-[16px] bg-center ${icon}`} />
              </div>
              <h2
                className={`truncate text-sm font-semibold ${textColorTitle} self-center`}
              >
                {GetTitle(estimationMethod)}
              </h2>
            </div>
            <div className="flex flex-row gap-2 ">
              {showPill && <Badge type={cardType}>{GetPillText(estimationMethod)}</Badge>}
              <div className="text-lg">
                {isCollapsed ? <HiChevronUp /> : <HiChevronDown />}
              </div>
            </div>
          </div>
        </button>
        {!isCollapsed && (
          <div className="gap-2">
            <div className={`text-sm font-normal text-neutral-600 dark:text-neutral-400`}>
              {cardType != 'outage' && GetBodyText(estimationMethod)}
              {cardType == 'outage' && <OutageMessage outageData={outageMessage} />}
            </div>
            {showMethodologyLink && (
              <div className="">
                <a
                  href="https://www.electricitymaps.com/methodology"
                  target="_blank"
                  rel="noreferrer"
                  className={`text-sm font-semibold text-black underline dark:text-white`}
                >
                  <span className="underline">Read about our estimation models</span>
                </a>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function OutageCard({ outageMessage }: { outageMessage: ZoneDetails['zoneMessage'] }) {
  return (
    <BaseCard
      estimationMethod={'outage'}
      outageMessage={outageMessage}
      icon="bg-[url('/images/estimated_light.svg')] dark:bg-[url('/images/estimated_dark.svg')]"
      showMethodologyLink={true}
      showPill={true}
      cardType="outage"
      bgColorClasses="bg-amber-700/20 dark:bg-amber-500/20"
      textColorTitle="text-amber-700 dark:text-amber-500"
    />
  );
}

function AggregatedCard() {
  return (
    <BaseCard
      estimationMethod={'aggregated'}
      outageMessage={undefined}
      icon="bg-[url('/images/aggregated_light.svg')] dark:bg-[url('/images/aggregated_dark.svg')]"
      showMethodologyLink={false}
      showPill={false}
      cardType="aggregated"
      bgColorClasses="bg-neutral-100 dark:bg-gray-800"
      textColorTitle="text-black dark:text-white"
    />
  );
}

function AggregatedEstimatedCard() {
  return (
    <BaseCard
      estimationMethod={'aggregated_estimated'}
      outageMessage={undefined}
      icon="bg-[url('/images/aggregated_light.svg')] dark:bg-[url('/images/aggregated_dark.svg')]"
      showMethodologyLink={false}
      showPill={true}
      cardType="aggregate_estimated"
      bgColorClasses="bg-neutral-100 dark:bg-gray-800"
      textColorTitle="text-black dark:text-white"
    />
  );
}

function EstimatedCard({ estimationMethod }: { estimationMethod: string | undefined }) {
  return (
    <BaseCard
      estimationMethod={estimationMethod}
      outageMessage={undefined}
      icon="bg-[url('/images/estimated_light.svg')] dark:bg-[url('/images/estimated_dark.svg')]"
      showMethodologyLink={true}
      showPill={true}
      cardType="estimated"
      bgColorClasses="bg-neutral-100 dark:bg-gray-800"
      textColorTitle="text-amber-700 dark:text-amber-500"
    />
  );
}

function truncateString(string_: string, number_: number) {
  return string_.length <= number_ ? string_ : string_.slice(0, number_) + '...';
}

function OutageMessage({
  outageData: outageData,
}: {
  outageData: ZoneDetails['zoneMessage'];
}) {
  if (!outageData || !outageData.message) {
    return null;
  }
  return (
    <span className="inline overflow-hidden">
      {truncateString(outageData.message, 300)}{' '}
      {outageData?.issue && outageData.issue != 'None' && (
        <span className="inline-flex">
          - see{' '}
          <a
            className="inline-flex"
            href={`https://github.com/electricitymaps/electricitymaps-contrib/issues/${outageData.issue}`}
          >
            <span className="pl-1 text-blue-600 underline">
              issue #{outageData.issue}
            </span>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              className="ml-1"
            >
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
          </a>
        </span>
      )}
    </span>
  );
}
