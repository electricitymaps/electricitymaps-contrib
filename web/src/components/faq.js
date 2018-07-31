const translation = require('../helpers/translation');
const formatting  = require('../helpers/formatting');

const d3 = Object.assign(
  {},
  require('d3-selection'),
);

// this faq object can be moved to translation files at a later date, once we are 100% agreed on its contents
const faq = {
  theMap: {
    groupName: 'The map',
    entries: {
      mapColors: {
        question: 'What do the colors on the map mean?',
        answer: 'We color areas on the map by the amounts of greenhouse gases that is emitted for each unit of electricity consumed there (its <a href="#carbonIntensity" class="entry-link">carbon intensity</a>). Greener colours means more climate friendly electricity consumption.',
      },
      mapArrows: {
        question: 'What do the arrows between areas on the map indicate?',
        answer: 'Arrows between the areas indicate the physical flow (imports and exports) of electricity between areas: the faster they blink, the faster the flow. The flow of electricity is important, because when you import some of your electricity from neighboring areas, you are also importing the carbon emissions associated with its production.',
      },
      mapSolarWindButtons: {
        question: 'What do “sun” and “wind” buttons on the map do?',
        answer: 'These buttons toggle the display of real-time wind speeds and sunsine strength, giving an indication of the potential for transitioning to solar and wind based energy alternatives in different areas. Note that this is just a superficial indication, as the actual potential in installing wind turbines and solar cells also is dependent on many other factors.',
      },
      mapNuclearColors: {
        question: 'Why are nuclear-powered countries shown as green on the map?',
        answer: 'Nuclear energy production has a very low carbon intensity (<a href="https://en.wikipedia.org/wiki/Life-cycle_greenhouse-gas_emissions_of_energy_sources#2014_IPCC.2C_Global_warming_potential_of_selected_electricity_sources"  target="_blank" >source</a>), and nuclear-powered countries are therefore shown as green on the map. This does not mean that there are not other environmental challenges associated nuclear energy (as is also the case with other forms of energy production), but these challenges are unrelated to the emissions of greenhouse gases and are therefore outside the scope of this map.',
      },
      mapColorBlind: {
        question: 'I am color blind. How can I read your map?',
        answer: 'You can change the colours displayed in the map by enabling the “color blind mode” setting. It is located on the bottom of the left panel on desktop and in the information tab on the mobile app.',
      },
    },
  },
  mapAreas: {
    groupName: 'Areas in the map',
    entries: {
      noData: {
        question: 'Why is data for my area not available?',
        answer: ' Either because the area\'s data sources are temporarily unavailable, or because we do not yet have any data sources setup for the area. You can <a href="#contribute" class="entry-link">help us with adding new data sources</a>.',
      },
      whySmallAreas: {
        question: 'Why do you divide the world into smaller areas and not simply show country averages?',
        answer: 'The areas are the smallest geographical areas we have data for. By having access to information at the highest level of granularity, electricity consumers in different areas can have a more precise knowledge about the origin of the electricity they are consuming, and its associated climate impact.',
      },
      divideExistingArea: {
        question: 'Can you divide my area into smaller parts?',
        answer: 'Sure, if there exists separate data sources for each part of the area. You can <a href="#contribute" class="entry-link">help us with adding new data sources</a>',
      },
      seeHistoricalData: {
        question: 'Can I see the history for an area further back in time than 24 hours?',
        answer: 'You can purchase access to all of our historical data through our <a href="https://data.electricitymap.org?utm_source=electricitymap.org&utm_medium=referral" target="_blank">database</a>.',
      },
    },
  },
  methodology: {
    groupName: 'Our methods',
    entries: {
      carbonIntensity: {
        question: 'What is "carbon intensity"?',
        answer: 'Carbon intensity is a measure of the greenhouse gas emissions associated with producing the electricity you consume (in gCO2eq/kWh - grams of carbon dioxide equivalents emitted per kilowatt hour of electricity consumed). <br><br>We measure the emissions of electricity consumption (not production), meaning all greenhouse gas emissions (both CO2 and other greenhouse gases such as methane) that has gone into producing the electricity which is being consumed in an area, taking into account the carbon intensities of the electricity imported from other areas. We use a life cycle analysis (LCA) approach, meaning that we take into account emissions arising from the whole life cycle of power plants (construction, fuel production, operational emissions, and decommissioning).',
      },
      consumptionFocus: {
        question: 'Why do you calculate the carbon intensity of electricity consumption instead of production?',
        answer: 'We believe citizens should be responsible for the electricity they consume, and not for the electricity that is produced in the area that they happen to live in. Furthermore, we believe areas should not be able to \'fake\' a low climate impact simply by relocating dirty energy production to other areas and then import the electricity from those areas.',
      }, 
      renewableLowCarbonDifference: {
        question: 'What is the difference between “renewable” and “low-carbon”?',
        answer: 'Renewable energy production is based on renewable energy sources such as wind and water flow, sunshine,  and geothermal energy. Low-carbon energy production means that the production involves a very low level of greenhouse gas emissions, such as in nuclear power production.',
      },
      importsAndExports: {
        question: 'Do you take into account imports and exports of electricity?',
        answer: 'Yes, we do. Imports and exports can be see on the map as small arrows between different areas [link to question about arrows]. Detailed information can be seen in the charts shown when you click on an area.',
      },
      emissionsOfStored: {
        question: 'What about emissions from generating electricity which is then stored in batteries or used to fill reservoirs?',
        answer: 'As currently only a small proportion of electricity is stored, inaccuracies in the modelling of these emissions should not make much difference to the total at present. However given the increasing importance of storage we hope to take it into account more fully in our model shortly.',
      },
      guaranteesOfOrigin: {
        question: 'What are green certificates, and how are they taken into account?',
        answer: 'When producers of renewable energy produce electricity, they can create Guarantees of Origin (or Renewable Energy Certificates) - a proof that renewable electricity has been produced and distributed into the power grid. These guarantees can then be sold, giving other non-renewable electricity producers a way to "compensate" for their emissions and the right to claim that the electricity they produce comes from renewable sources, regardless of its actual, physical source.<br><br> This means that electricity consumers can be told that their electricity is green, when this is not true in the physical sense. This problematic, as it removes consumer incentives to consume electricity at the best time (for instance when the amount of renewable electricity in the grid is at its highest). This map therefore excludes Guarantees of Origin, instead offering a location-based, physical picture of the power grid, in order to responsibilize consumers.',
      },
      otherSources: {
        question: 'Why don’t you show other sources of emissions than electricity production?',
        answer: 'This would be outside of the scope of this project. However, at Tomorrow we are actively working on developing <a href="#whoAreYou" class="entry-link">new solutions for quantifying the climate impact of your everyday decisions</a>.',
      },
      homeSolarPanel: {
        question: 'What if I have a solar panel installed in my home?',
        answer: 'We measure the carbon intensity of the local power grid, so any electricity you consume directly from your solar panel (off-grid) is not a part our measurements. However, if your solar panel is providing power to your local power grid, its production is included in our statistics in areas where estimations of local solar energy production is made publically available (such as in France and in the UK).',
      },
      emissionsPerCapita: {
        question: 'Why don\'t you show emissions per capita?',
        answer: 'Some of the electricity consumed in an area is used in for manufacturing of physical goods and products which are later exported and consumed in other areas. This manufacturing, and therefore also its electricity consumption and associated emissions, is driven by the consumption of products in the <em>importing areas</em>, not in the area where the production is taking place. We believe people should only be responsible for what they consume, not for products manufactured in the area they live in that they do not consume it themselves. In this sense, showing per capita emissions of electricity consumption for areas is misleading.',
      },
    },
  },
  data: {
    groupName: 'Our data',
    entries: {
      dataOrigins: {
        question: 'How do you get your data?',
        answer: 'We compute all of our data from publically available data, published by electricity grid operators, official agencies, and others. You can click on an area to see more specifics on the origins of its data.',
      },
      dataDownload: {
        question: 'Can I download your data?',
        answer: 'You can purchase access to all of our data in our <a href="https://data.electricitymap.org?utm_source=electricitymap.org&utm_medium=referral" target="_blank">database</a>.',
      },
      dataIntegration: {
        question: 'Can I integrate your data real-time into my application or device?',
        answer: 'Yes! We sell access to a <a href="https://api.electricitymap.org?utm_source=electricitymap.org&utm_medium=referral" target="_blank">real-time API</a>, which includes future forecasts.',
      }
    },
  },
  aboutUs: {
    groupName: 'About us',
    entries: {
      whoAreYou: {
        question: 'Who are you?',
        answer: 'The Electricity Map is developed and maintained by <a href="https://www.tmrow.com/" target="_blank">Tomorrow</a>, a small Danish/French start-up company. Our goal is to help humanity reach a sustainable state of existence by quantifying, and making widely accessible, the climate impact of the daily choices we make.',
      },
      feedback: {
        question: 'Can I give you some feedback?',
        answer: 'Please do! Please fill out <a href="https://docs.google.com/forms/d/e/1FAIpQLSc-_sRr3mmhe0bifigGxfAzgh97-pJFcwpwWZGLFc6vvu8laA/viewform?c=0&w=1" target="_blank">our feedback form</a> or <a href="mailto:hello@tmrow.com">send us an email!</a>',
      },
      contribute: {
        question: 'Can I contribute to your project?',
        answer: ' Yes! The Electricity Map is an open-source project, made possible by our volunteer contributors. If you want to help develop the map, either by adding data sources for new areas, adding new features or fixing bugs, feel free to join us in our <a href="https://github.com/corradio/electricitymap/" target="_blank">github</a>.',
      },
      workTogether: {
        question: 'Can we work together?',
        answer: 'We are actively looking for new opportunities to collaborate. <a href="mailto:hello@tmrow.com">Send us an email!</a>',
      },
      disclaimer: {
        question: 'Disclaimer',
        answer: '<a href="https://www.tmrow.com/" target="_blank">Tomorrow</a> publishes data and images on the <a href="https://www.electricitymap.org/" target="_blank">electricityMap</a> for information purposes. It makes no claims of correctness nor provides any form of warranties, and reserves the right to change the content at any time or to remove parts without having to inform you of this. Tomorrow assumes no responsibility for, and shall not be liable for, any damages or expenses you may incur as a result of any inaccuracy, incompleteness, untimeliness or obsolescence of the electricityMap, or the information derived from them.  It is not allowed to include this webpage, or any of its individual elements, in another webpage, without formal prior written consent.<br><br> All intellectual property rights belong to the rightful owners and its licensors. Copying, distribution and any other use of these materials, in particular the energy data, is not permitted without the written permission of Tomorrow, except and only to the extent otherwise provided in regulations of mandatory law (such as the right to quote), unless specified otherwise for specific materials. <br><br>This disclaimer may be updated from time to time.'
      },
    },
  },
};

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
    }
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
    }
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
