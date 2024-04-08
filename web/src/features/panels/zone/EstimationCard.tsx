import Badge from 'components/Badge';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useAtom } from 'jotai';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { HiChevronDown, HiChevronUp } from 'react-icons/hi2';
import { ZoneDetails } from 'types';
import {
  feedbackCardCollapsedNumberAtom,
  hasEstimationFeedbackBeenSeenAtom,
} from 'utils/state/atoms';

import FeedbackCard from './FeedbackCard';
import { showEstimationFeedbackCard } from './util';

export default function EstimationCard({
  cardType,
  estimationMethod,
  estimatedPercentage,
  outageMessage,
}: {
  cardType: string;
  estimationMethod?: string;
  estimatedPercentage?: number;
  outageMessage: ZoneDetails['zoneMessage'];
}) {
  const [isFeedbackCardVisibile, setIsFeedbackCardVisibile] = useState(false);
  const [feedbackCardCollapsedNumber, _] = useAtom(feedbackCardCollapsedNumberAtom);
  const feedbackEnabled = useFeatureFlag('feedback-estimation-labels');
  const [hasFeedbackCardBeenSeen, setHasFeedbackCardBeenSeen] = useAtom(
    hasEstimationFeedbackBeenSeenAtom
  );

  useEffect(() => {
    setIsFeedbackCardVisibile(
      feedbackEnabled &&
        showEstimationFeedbackCard(
          feedbackCardCollapsedNumber,
          isFeedbackCardVisibile,
          hasFeedbackCardBeenSeen,
          setHasFeedbackCardBeenSeen
        )
    );
  }, [feedbackEnabled, feedbackCardCollapsedNumber]);

  switch (cardType) {
    case 'outage': {
      return <OutageCard outageMessage={outageMessage} />;
    }
    case 'aggregated': {
      return <AggregatedCard estimatedPercentage={estimatedPercentage} />;
    }
    case 'estimated': {
      return (
        <div>
          <EstimatedCard estimationMethod={estimationMethod} />
          {isFeedbackCardVisibile && <FeedbackCard estimationMethod={estimationMethod} />}
        </div>
      );
    }
  }
}

function getEstimationTranslation(
  field: 'title' | 'pill' | 'body',
  estimationMethod?: string,
  estimatedPercentage?: number
) {
  const { t } = useTranslation();
  const exactTranslation =
    (estimatedPercentage ?? 0) > 0 && estimationMethod === 'aggregated'
      ? t(`estimation-card.aggregated_estimated.${field}`, {
          percentage: estimatedPercentage,
        })
      : t(`estimation-card.${estimationMethod?.toLowerCase()}.${field}`);

  const genericTranslation = t(`estimation-card.estimated_generic_method.${field}`);
  return exactTranslation.startsWith('estimation-card.')
    ? genericTranslation
    : exactTranslation;
}

function BaseCard({
  estimationMethod,
  estimatedPercentage,
  outageMessage,
  icon,
  iconPill,
  showMethodologyLink,
  pillType,
  textColorTitle,
}: {
  estimationMethod?: string;
  estimatedPercentage?: number;
  outageMessage: ZoneDetails['zoneMessage'];
  icon: string;
  iconPill?: string;
  showMethodologyLink: boolean;
  pillType?: string;
  textColorTitle: string;
}) {
  const [isCollapsed, setIsCollapsed] = useState(
    estimationMethod == 'outage' ? false : true
  );

  const [feedbackCardCollapsedNumber, setFeedbackCardCollapsedNumber] = useAtom(
    feedbackCardCollapsedNumberAtom
  );

  const handleToggleCollapse = () => {
    setFeedbackCardCollapsedNumber(feedbackCardCollapsedNumber + 1);
    setIsCollapsed((previous) => !previous);
  };
  const { t } = useTranslation();

  const title = getEstimationTranslation('title', estimationMethod);
  const pillText = getEstimationTranslation(
    'pill',
    estimationMethod,
    estimatedPercentage
  );
  const bodyText = getEstimationTranslation(
    'body',
    estimationMethod,
    estimatedPercentage
  );
  const showBadge =
    estimationMethod == 'aggregated'
      ? Boolean(estimatedPercentage)
      : pillType != undefined;

  return (
    <div
      className={`w-full rounded-lg px-3 py-2.5 ${
        estimationMethod == 'outage'
          ? 'bg-amber-700/20 dark:bg-amber-500/20'
          : 'bg-neutral-100 dark:bg-gray-800'
      } mb-4 gap-2 border border-neutral-200 transition-all dark:border-gray-700`}
    >
      <div className="flex flex-col">
        <button data-test-id="collapse-button" onClick={handleToggleCollapse}>
          <div className="flex flex-row items-center justify-between">
            <div className="flex w-2/3 flex-initial flex-row gap-2">
              <div className={`flex items-center justify-center`}>
                <div className={`h-[16px] w-[16px] bg-center ${icon}`} />
              </div>
              <h2
                className={`text-left text-sm font-semibold ${textColorTitle} self-center`}
                data-test-id="title"
              >
                {title}
              </h2>
            </div>
            <div className="flex h-fit flex-row gap-2 text-nowrap">
              {showBadge && (
                <Badge type={pillType} icon={iconPill} pillText={pillText}></Badge>
              )}
              <div className="text-lg">
                {isCollapsed ? (
                  <div data-test-id="collapse-down">
                    <HiChevronDown />
                  </div>
                ) : (
                  <div data-test-id="collapse-up">
                    <HiChevronUp />
                  </div>
                )}
              </div>
            </div>
          </div>
        </button>
        {!isCollapsed && (
          <div className="gap-2 pt-1.5">
            <div
              data-test-id="body-text"
              className={`text-sm font-normal text-neutral-600 dark:text-neutral-400`}
            >
              {estimationMethod != 'outage' && bodyText}
              {estimationMethod == 'outage' && (
                <OutageMessage outageData={outageMessage} />
              )}
            </div>
            {showMethodologyLink && (
              <div className="">
                <a
                  href="https://www.electricitymaps.com/methodology"
                  target="_blank"
                  rel="noreferrer"
                  data-test-id="methodology-link"
                  className={`text-sm font-semibold text-black underline dark:text-white`}
                >
                  <span className="underline">{t(`estimation-card.link`)}</span>
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
      iconPill="h-[12px] w-[12px] mt-[1px] bg-[url('/images/warning_light.svg')] bg-center dark:bg-[url('/images/warning_dark.svg')]"
      showMethodologyLink={false}
      pillType="warning"
      textColorTitle="text-amber-700 dark:text-amber-500"
    />
  );
}

function AggregatedCard({ estimatedPercentage }: { estimatedPercentage?: number }) {
  return (
    <BaseCard
      estimationMethod={'aggregated'}
      estimatedPercentage={estimatedPercentage}
      outageMessage={undefined}
      icon="bg-[url('/images/aggregated_light.svg')] dark:bg-[url('/images/aggregated_dark.svg')]"
      iconPill={undefined}
      showMethodologyLink={false}
      pillType={'warning'}
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
      iconPill={undefined}
      showMethodologyLink={true}
      pillType="default"
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
        <span className="mt-1 inline-flex">
          See{' '}
          <a
            className="inline-flex text-sm font-semibold text-black underline dark:text-white"
            href={`https://github.com/electricitymaps/electricitymaps-contrib/issues/${outageData.issue}`}
          >
            <span className="pl-1 underline">issue #{outageData.issue}</span>
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
