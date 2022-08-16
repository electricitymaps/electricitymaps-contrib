import React, { useState, useRef } from 'react';
import styled from 'styled-components';

import { useTranslation } from '../helpers/translation';
import Icon from './icon';

const TermsAndPrivacyContainer = styled.div`
  @media (max-width: 767px) {
    display: none;
  }
  text-align: left;
  box-shadow: 0 0 6px 1px rgb(0 0 0 / 10%);

  a {
    margin-right: 1rem;
  }
`;

const orderings = [
  {
    groupKey: 'theMap',
    entryOrder: ['mapColors', 'mapArrows', 'mapSolarWindButtons', 'mapNuclearColors', 'mapColorBlind'],
  },
  {
    groupKey: 'mapAreas',
    entryOrder: ['noData', 'whySmallAreas', 'divideExistingArea', 'seeHistoricalData'],
  },
  {
    groupKey: 'methodology',
    entryOrder: [
      'carbonIntensity',
      'consumptionFocus',
      'renewableLowCarbonDifference',
      'importsAndExports',
      'guaranteesOfOrigin',
      'otherSources',
      'homeSolarPanel',
      'emissionsPerCapita',
    ],
  },
  {
    groupKey: 'data',
    entryOrder: ['dataOrigins', 'dataDownload', 'dataIntegration'],
  },
  {
    groupKey: 'aboutUs',
    entryOrder: ['whoAreYou', 'feedback', 'contribute', 'workTogether', 'disclaimer'],
  },
];

const QuestionAnswer = ({ answerVisible, setAnswerVisible, groupKey, entryKey }: any) => {
  const { __ } = useTranslation();
  return (
    <div className="question-answer-container" id={entryKey}>
      <button
        className="question"
        onClick={() => setAnswerVisible(entryKey, !answerVisible)}
        id={`${groupKey}.${entryKey}-question`}
        aria-controls={`${groupKey}.${entryKey}-answer`}
        aria-expanded={answerVisible}
      >
        {/* @ts-expect-error TS(2322): Type '{ iconName: string; }' is not assignable to ... Remove this comment to see the full error message */}
        <Icon iconName={answerVisible ? 'expand_less' : 'expand_more'} />
        <span>{__(`${groupKey}.${entryKey}-question`)}</span>
      </button>
      {answerVisible && (
        <div
          id={`${groupKey}.${entryKey}-answer`}
          role="region"
          aria-labelledby={`${groupKey}.${entryKey}-question`}
          className="answer"
          dangerouslySetInnerHTML={{
            __html: __(`${groupKey}.${entryKey}-answer`),
          }}
        />
      )}
    </div>
  );
};

const FAQ = ({ className }: any) => {
  const [answersVisible, setAnswersVisible] = useState({});
  const { __ } = useTranslation();
  const setAnswerVisible = (entryKey: any, value: any) => {
    setAnswersVisible(Object.assign({}, answersVisible, { [entryKey]: value }));
  };

  // 50ms after every render go through all the links in the answers
  // and make sure the ones which reference different FAQ sections
  // also update the answersVisible state.
  // TODO: Update answersVisible state idiomatically from the URL
  // once React Router integration is in place.
  // See https://github.com/tmrowco/electricitymap-contrib/issues/2161.
  const ref = useRef(null);
  setTimeout(() => {
    if (ref && ref.current) {
      const links = (ref.current as any).querySelectorAll('.entry-link');
      // This seems to be the most browser-compatible way to iterate through a list of nodes.
      // See: https://developer.mozilla.org/en-US/docs/Web/API/NodeList#Example.
      Array.prototype.forEach.call(links, (link) => {
        const entryKey = link.href.split('#')[1];
        if (entryKey) {
          link.onclick = () => {
            setAnswerVisible(entryKey, true);
          };
        }
      });
    }
  }, 50);

  return (
    <React.Fragment>
      <div className={className} ref={ref}>
        <div className="faq-container">
          {orderings.map(({ groupKey, entryOrder }) => (
            <div className="question-group-container" key={groupKey}>
              <div className="question-group-header title">{__(`${groupKey}.groupName`)}</div>
              {entryOrder.map((entryKey) => (
                <QuestionAnswer
                  key={entryKey}
                  groupKey={groupKey}
                  entryKey={entryKey}
                  setAnswerVisible={setAnswerVisible}
                  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
                  answerVisible={answersVisible[entryKey]}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
      <TermsAndPrivacyContainer>
        <a href="https://www.electricitymaps.com/privacy-policy/">{__('misc.privacyPolicy')}</a>
        <a href="https://www.electricitymaps.com/legal-notice/">{__('misc.legalNotice')}</a>
      </TermsAndPrivacyContainer>
    </React.Fragment>
  );
};

export default FAQ;
