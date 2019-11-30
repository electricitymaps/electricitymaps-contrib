const d3 = Object.assign(
  {},
  require('d3-selection'),
);

const translation = require('../helpers/translation');
const formatting = require('../helpers/formatting');

const faq = {};

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

orderings.forEach((e) => {
  faq[e.groupKey] = {
    groupName: translation.translate(`${e.groupKey}.groupName`),
    entries: {},
  };
  e.entryOrder.forEach((f) => {
    faq[e.groupKey].entries[f] = {
      question: translation.translate(`${e.groupKey}.${f}-question`),
      answer: translation.translate(`${e.groupKey}.${f}-answer`),
    };
  });
});

export default class FAQ {
  constructor(selectorId) {
    this.selector = d3.select(selectorId);
    this._setup();
  }

  _setup() {
    this.container = this.selector.append('div').attr('class', 'faq-container');
    this.domElements = [];
    orderings.forEach((questionGroup) => {
      this._createQuestionGroup(questionGroup.groupKey, questionGroup.entryOrder, questionGroup.entryLinks);
    });
  }

  _createQuestionGroup(groupKey, groupEntryOrder, groupEntryLinks) {
    const groupContainer = this.container.append('div').attr('class', 'question-group-container');
    const groupHeader = groupContainer.append('div').attr('class', 'question-group-header title');
    groupHeader.text(faq[groupKey].groupName);

    groupEntryOrder.forEach((entryKey) => {
      const questionEntryTexts = faq[groupKey].entries[entryKey];
      const answerLinkTargetEntryId = groupEntryLinks && groupEntryLinks[entryKey];
      this._createQuestionAndAnswer(groupContainer, questionEntryTexts, entryKey, answerLinkTargetEntryId);
    });
  }

  _createQuestionAndAnswer(groupContainer, questionEntryTexts, entryKey, answerLinkTargetEntryId) {
    const entryContainer = groupContainer.append('div').attr('class', 'question-answer-container').attr('id', entryKey);
    const questionContainer = entryContainer.append('div').attr('class', 'question');
    questionContainer.append('i').attr('class', 'material-icons').text('expand_more');
    questionContainer.append('span').text(questionEntryTexts.question);
    const answer = entryContainer.append('div').attr('class', 'answer').html(formatting.co2Sub(questionEntryTexts.answer));
    if (answerLinkTargetEntryId) {
      answer.selectAll('.entry-link').on('click', () => {
        this._toggleAnswer(answerLinkTargetEntryId);
      });
    }
    questionContainer.on('click', () => this._toggleAnswer(entryKey));
  }

  _toggleAnswer(id) {
    const entry = d3.selectAll(`#${id}`);
    if (entry.nodes().length) {
      const answer = entry.selectAll('.answer');
      const answerVisible = !answer.classed('visible');
      answer.classed('visible', answerVisible);
      entry.selectAll('.material-icons').text(answerVisible ? 'expand_less' : 'expand_more');
    }
  }
}
