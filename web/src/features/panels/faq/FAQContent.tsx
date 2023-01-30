import * as Accordion from '@radix-ui/react-accordion';
import { HiChevronRight } from 'react-icons/hi2';
import { useTranslation } from 'translation/translation';

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

function FAQContent() {
  const { __ } = useTranslation();

  return (
    <Accordion.Root type="multiple" className="space-y-4  pr-2">
      {orderings.map(({ groupKey, entryOrder }) => (
        <div key={`group-${groupKey}`} className="space-y-2">
          <h3 className="font-bold">{__(`${groupKey}.groupName`)}</h3>
          {entryOrder.map((entryKey, index) => (
            <Accordion.Item
              value={`${groupKey}-item-${index + 1}`}
              key={`header-${index}`}
              className="overflow-hidden"
            >
              <Accordion.Header className="w-full">
                <Accordion.Trigger className="group flex items-center space-x-2 text-left hover:text-gray-600 dark:hover:text-gray-400">
                  <HiChevronRight className="flex-none duration-300 group-radix-state-open:rotate-90" />{' '}
                  <span>{__(`${groupKey}.${entryKey}-question`)}</span>
                </Accordion.Trigger>
              </Accordion.Header>
              <Accordion.Content className="ml-2 border-l border-gray-300 pl-4 radix-state-closed:animate-slide-up radix-state-open:animate-slide-down">
                <div
                  className="prose prose-sm text-md leading-5 dark:prose-invert"
                  dangerouslySetInnerHTML={{
                    __html: __(`${groupKey}.${entryKey}-answer`),
                  }}
                />
              </Accordion.Content>
            </Accordion.Item>
          ))}
        </div>
      ))}
    </Accordion.Root>
  );
}

export default FAQContent;
