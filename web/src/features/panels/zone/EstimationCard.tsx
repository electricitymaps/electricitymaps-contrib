import useGetState from 'api/getState';
import Accordion from 'components/Accordion';
import FeedbackCard, { SurveyResponseProps } from 'components/app-survey/FeedbackCard';
import { useFeatureFlag } from 'features/feature-flags/api';
import { useEvents, useTrackEvent } from 'hooks/useTrackEvent';
import { useAtom, useAtomValue } from 'jotai';
import { ChartNoAxesColumn, CircleDashed, TrendingUpDown } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaGithub } from 'react-icons/fa6';
import { ZoneMessage } from 'types';
import { EstimationMethods, isTSAModel } from 'utils/constants';
import getEstimationOrAggregationTranslation from 'utils/getEstimationTranslation';
import {
  feedbackCardCollapsedNumberAtom,
  hasEstimationFeedbackBeenSeenAtom,
  isHourlyAtom,
  selectedDatetimeStringAtom,
} from 'utils/state/atoms';

import { showEstimationFeedbackCard } from './util';

function postSurveyResponse({
  feedbackScore,
  inputText,
  reference: surveyReference,
}: SurveyResponseProps) {
  fetch(`https://hooks.zapier.com/hooks/catch/14671709/3l9daod/`, {
    method: 'POST',
    body: JSON.stringify({
      score: feedbackScore,
      feedback: inputText,
      reference: surveyReference,
    }),
  });
}

function getCardType({
  estimationMethod,
  zoneMessage,
  isHourly,
}: {
  estimationMethod?: EstimationMethods;
  zoneMessage?: ZoneMessage;
  isHourly: boolean;
}): 'estimated' | 'aggregated' | 'outage' | 'none' {
  if (
    (zoneMessage !== undefined &&
      zoneMessage?.message !== undefined &&
      zoneMessage?.issue !== undefined) ||
    estimationMethod === EstimationMethods.THRESHOLD_FILTERED
  ) {
    return 'outage';
  }
  if (!isHourly) {
    return 'aggregated';
  }
  if (estimationMethod) {
    return 'estimated';
  }
  return 'none';
}

export default function EstimationCard({
  zoneKey,
  estimatedPercentage,
  zoneMessage,
}: {
  zoneKey: string;
  estimatedPercentage?: number;
  zoneMessage?: ZoneMessage;
}) {
  const { t } = useTranslation();
  const { data } = useGetState();
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const isHourly = useAtomValue(isHourlyAtom);
  const [isFeedbackCardVisible, setIsFeedbackCardVisible] = useState(false);
  const feedbackCardCollapsedNumber = useAtomValue(feedbackCardCollapsedNumberAtom);
  const feedbackEnabled = useFeatureFlag('feedback-estimation-labels');

  const [hasFeedbackCardBeenSeen, setHasFeedbackCardBeenSeen] = useAtom(
    hasEstimationFeedbackBeenSeenAtom
  );

  useEffect(() => {
    setIsFeedbackCardVisible(
      feedbackEnabled &&
        showEstimationFeedbackCard(
          feedbackCardCollapsedNumber,
          isFeedbackCardVisible,
          hasFeedbackCardBeenSeen,
          setHasFeedbackCardBeenSeen
        )
    );
  }, [
    feedbackEnabled,
    feedbackCardCollapsedNumber,
    isFeedbackCardVisible,
    hasFeedbackCardBeenSeen,
    setHasFeedbackCardBeenSeen,
  ]);

  if (!data || !selectedDatetimeString || !zoneKey) {
    return null;
  }
  const selectedData = data?.datetimes[selectedDatetimeString]?.z[zoneKey];

  const estimationMethod = selectedData?.em || undefined;

  const isAggregated = !isHourly;

  if (!estimationMethod && !isAggregated) {
    return null;
  }
  const isTSA = estimationMethod ? isTSAModel(estimationMethod) : false;
  const cardType = getCardType({
    estimationMethod,
    zoneMessage,
    isHourly,
  });

  if (cardType === 'none') {
    return null;
  }

  switch (cardType) {
    case 'outage': {
      return <OutageCard zoneMessage={zoneMessage} estimationMethod={estimationMethod} />;
    }
    case 'aggregated': {
      return <AggregatedCard estimatedPercentage={estimatedPercentage} />;
    }
    case 'estimated': {
      return (
        <div>
          {isTSA ? (
            <EstimatedTSACard />
          ) : (
            <EstimatedCard estimationMethod={estimationMethod} />
          )}
          {isFeedbackCardVisible && isTSA && (
            <FeedbackCard
              surveyReference={estimationMethod}
              postSurveyResponse={postSurveyResponse}
              primaryQuestion={t('feedback-card.estimations.primary-question')}
              secondaryQuestionHigh={t('feedback-card.estimations.secondary-question')}
              secondaryQuestionLow={t('feedback-card.estimations.secondary-question')}
              subtitle={t('feedback-card.estimations.subtitle')}
            />
          )}
        </div>
      );
    }
  }
}

function BaseCard({
  estimationMethod,
  estimatedPercentage,
  zoneMessage,
  icon,
  showMethodologyLink,
  textColorTitle,
  cardType,
}: {
  estimationMethod?: EstimationMethods;
  estimatedPercentage?: number;
  zoneMessage?: ZoneMessage;
  icon: React.ReactElement;
  showMethodologyLink: boolean;
  textColorTitle: string;
  cardType: string;
}) {
  const [feedbackCardCollapsedNumber, setFeedbackCardCollapsedNumber] = useAtom(
    feedbackCardCollapsedNumberAtom
  );
  const isCollapsedDefault = estimationMethod === 'outage' ? false : true;
  const [isCollapsed, setIsCollapsed] = useState(isCollapsedDefault);
  const isHourly = useAtomValue(isHourlyAtom);
  const isAggregated = !isHourly;

  const trackEvent = useTrackEvent();
  const { trackMissingDataMethodology } = useEvents(trackEvent);

  const trackToggle = () => {
    setFeedbackCardCollapsedNumber(feedbackCardCollapsedNumber + 1);
  };
  const { t } = useTranslation();

  const title = getEstimationOrAggregationTranslation(
    t,
    'title',
    isAggregated,
    estimationMethod
  );

  const bodyText = getEstimationOrAggregationTranslation(
    t,
    'body',
    isAggregated,
    estimationMethod,
    estimatedPercentage
  );

  return (
    <div
      className={`w-full rounded-2xl px-3 py-1.5 ${
        estimationMethod == 'outage'
          ? 'bg-warning/20 dark:bg-warning-dark/20'
          : 'bg-neutral-100/60 dark:bg-neutral-800/60'
      } mb-4 border border-neutral-200 transition-all dark:border-neutral-700`}
    >
      <Accordion
        onClick={() => trackToggle()}
        className={textColorTitle}
        icon={icon}
        title={title}
        isCollapsed={isCollapsed}
        setState={setIsCollapsed}
      >
        <div className="flex flex-col gap-2">
          <div
            data-testid="body-text"
            className={`text-sm font-normal text-neutral-600 dark:text-neutral-400`}
          >
            {estimationMethod != 'outage' && bodyText}
            {estimationMethod == 'outage' && (
              <ZoneMessageBlock zoneMessage={zoneMessage} />
            )}
          </div>
          {showMethodologyLink && (
            <a
              href="https://www.electricitymaps.com/methodology#missing-data"
              target="_blank"
              rel="noreferrer"
              data-testid="methodology-link"
              className={`text-sm font-semibold text-black underline dark:text-white`}
              onClick={trackMissingDataMethodology}
            >
              {t(`estimation-card.link`)}
            </a>
          )}
        </div>
      </Accordion>
    </div>
  );
}

export function OutageCard({
  zoneMessage,
  estimationMethod,
}: {
  zoneMessage?: ZoneMessage;
  estimationMethod?: string;
}) {
  const { t } = useTranslation();
  const zoneMessageText =
    estimationMethod === EstimationMethods.THRESHOLD_FILTERED
      ? { message: t(`estimation-card.${EstimationMethods.THRESHOLD_FILTERED}.body`) }
      : zoneMessage;
  return (
    <BaseCard
      estimationMethod={EstimationMethods.OUTAGE}
      zoneMessage={zoneMessageText}
      icon={<TrendingUpDown size={16} />}
      showMethodologyLink={false}
      textColorTitle="text-warning dark:text-warning-dark"
      cardType="outage-card"
    />
  );
}

export function AggregatedCard({
  estimatedPercentage,
}: {
  estimatedPercentage?: number;
}) {
  return (
    <BaseCard
      estimatedPercentage={estimatedPercentage}
      zoneMessage={undefined}
      icon={<ChartNoAxesColumn size={16} />}
      showMethodologyLink={false}
      textColorTitle="text-black dark:text-white"
      cardType="aggregated-card"
    />
  );
}

export function EstimatedCard({
  estimationMethod,
}: {
  estimationMethod: EstimationMethods | undefined;
}) {
  return (
    <BaseCard
      estimationMethod={estimationMethod}
      zoneMessage={undefined}
      icon={<TrendingUpDown size={16} />}
      showMethodologyLink={true}
      textColorTitle={'text-black dark:text-white'}
      cardType="estimated-card"
    />
  );
}

export function EstimatedTSACard() {
  return (
    <BaseCard
      estimationMethod={EstimationMethods.TSA}
      zoneMessage={undefined}
      icon={<CircleDashed size={16} />}
      showMethodologyLink={true}
      textColorTitle="text-black dark:text-white"
      cardType="estimated-card"
    />
  );
}

function truncateString(string_: string, number_: number) {
  return string_.length <= number_ ? string_ : string_.slice(0, number_) + '...';
}

function ZoneMessageBlock({ zoneMessage }: { zoneMessage?: ZoneMessage }) {
  const { t } = useTranslation();

  if (!zoneMessage || !zoneMessage.message) {
    return null;
  }

  return (
    <span className="inline overflow-hidden">
      {truncateString(zoneMessage.message, 300)}{' '}
      {zoneMessage?.issue && zoneMessage.issue != 'None' && (
        <span className="mt-1 inline-flex">
          <a
            className="inline-flex items-center gap-1 text-sm font-semibold text-black underline dark:text-white"
            href={`https://github.com/electricitymaps/electricitymaps-contrib/issues/${zoneMessage.issue}`}
          >
            <span className="pl-1 underline">{t('estimation-card.outage-details')}</span>
            <FaGithub size={18} />
          </a>
        </span>
      )}
    </span>
  );
}
