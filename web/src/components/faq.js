import React, { useState } from 'react';

import { __ } from '../helpers/translation';
import { co2Sub } from '../helpers/formatting';

const d3 = Object.assign(
  {},
  require('d3-selection'),
);

const orderings = [
  {
    groupKey: 'theMap',
    entryOrder: [
      'mapColors',
      'mapArrows',
      'mapSolarWindButtons',
      'mapNuclearColors',
      'mapColorBlind'],
    entryLinks: {
      // Links from one entry to another;
      // onClick link events are mapped to all links with the "entry-link" class
      mapColors: 'carbonIntensity',
    },
  },
  {
    groupKey: 'mapAreas',
    entryOrder: [
      'noData',
      'whySmallAreas',
      'divideExistingArea',
      'seeHistoricalData',
    ],
    entryLinks: {
      noData: 'contribute',
      divideExistingArea: 'contribute',
    },
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
    entryLinks: {
      otherSources: 'whoAreYou',
    },
  },
  {
    groupKey: 'data',
    entryOrder: [
      'dataOrigins',
      'dataDownload',
      'dataIntegration',
    ],
    entryLinks: {},
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
    entryLinks: {},
  },
];

const FAQ = ({ className }) => {
  const [answersVisible, setAnswersVisible] = useState({});

  const toggleQuestion = (entryKey, linkToEntryKey) => {
    setAnswersVisible(Object.assign({}, answersVisible, {
      [entryKey]: !answersVisible[entryKey],
    }));
    if (linkToEntryKey) {
      setTimeout(() => {
        d3.selectAll(`#${entryKey}`).selectAll('.entry-link').on('click', () => {
          setTimeout(() => {
            setAnswersVisible(Object.assign({}, answersVisible, {
              [entryKey]: true,
              [linkToEntryKey]: true,
            }));
          }, 50);
        });
      }, 50);
    }
  };


  return (
    <div className={className}>
      <div className="faq-container">
        {orderings.map(({ groupKey, entryOrder, entryLinks }) => (
          <div className="question-group-container" key={groupKey}>
            <div className="question-group-header title">
              {__(`${groupKey}.groupName`)}
            </div>
            {entryOrder.map((entryKey) => {
              const answerVisible = answersVisible[entryKey];
              const linkToEntryKey = entryLinks[entryKey];
              return (
                <div className="question-answer-container" id={entryKey} key={entryKey}>
                  <div
                    className="question"
                    onClick={() => toggleQuestion(entryKey, linkToEntryKey)}
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
                        __html: co2Sub(__(`${groupKey}.${entryKey}-answer`))
                      }}
                    />
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
};

export default FAQ;
