import React, { useState, useRef } from 'react';

import { __ } from '../helpers/translation';
import { co2Sub } from '../helpers/formatting';

const orderings = [
  {
    groupKey: 'theMap',
    entryOrder: [
      'mapColors',
      'mapArrows',
      'mapSolarWindButtons',
      'mapNuclearColors',
      'mapColorBlind',
    ],
  },
  {
    groupKey: 'mapAreas',
    entryOrder: [
      'noData',
      'whySmallAreas',
      'divideExistingArea',
      'seeHistoricalData',
    ],
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
    entryOrder: [
      'dataOrigins',
      'dataDownload',
      'dataIntegration',
    ],
  },
  {
    groupKey: 'aboutUs',
    entryOrder: [
      'whoAreYou',
      'feedback',
      'contribute',
      'workTogether',
      'disclaimer',
    ],
  },
];

const QuestionAnswer = ({
  answerVisible,
  setAnswerVisible,
  groupKey,
  entryKey,
}) => (
  <div className="question-answer-container" id={entryKey}>
    <div
      className="question"
      onClick={() => setAnswerVisible(entryKey, !answerVisible)}
    >
      <i className="material-icons">
        {answerVisible ? 'expand_less' : 'expand_more'}
      </i>
      <span>{__(`${groupKey}.${entryKey}-question`)}</span>
    </div>
    {answerVisible && (
      <div
        className="answer"
        dangerouslySetInnerHTML={{
          __html: co2Sub(__(`${groupKey}.${entryKey}-answer`)),
        }}
      />
    )}
  </div>
);

const FAQ = ({ className }) => {
  const [answersVisible, setAnswersVisible] = useState({});
  const setAnswerVisible = (entryKey, value) => {
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
      ref.current.querySelectorAll('.entry-link').forEach((link) => {
        const entryKey = link.href.split('#')[1];
        if (entryKey) {
          link.onclick = () => { setAnswerVisible(entryKey, true); };
        }
      });
    }
  }, 50);

  return (
    <div className={className} ref={ref}>
      <div className="faq-container">
        {orderings.map(({ groupKey, entryOrder }) => (
          <div className="question-group-container" key={groupKey}>
            <div className="question-group-header title">
              {__(`${groupKey}.groupName`)}
            </div>
            {entryOrder.map(entryKey => (
              <QuestionAnswer
                key={entryKey}
                groupKey={groupKey}
                entryKey={entryKey}
                setAnswerVisible={setAnswerVisible}
                answerVisible={answersVisible[entryKey]}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default FAQ;
