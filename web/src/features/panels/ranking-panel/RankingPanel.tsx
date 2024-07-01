import useGetState from 'api/getState';
import { HorizontalDivider } from 'components/Divider';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { ReactElement, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  productionConsumptionAtom,
  selectedDatetimeIndexAtom,
  spatialAggregateAtom,
} from 'utils/state/atoms';

import { getRankedState } from './getRankingPanelData';
import RankingPanelAccordion from './RankingPanelAccordion';
import SearchBar from './SearchBar';
import SocialIconRow from './SocialIcons';
import { VirtualizedZoneList } from './ZoneList';

export default function RankingPanel(): ReactElement {
  const { t } = useTranslation();
  const getCo2colorScale = useCo2ColorScale();
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [searchTerm, setSearchTerm] = useState('');
  const [electricityMode] = useAtom(productionConsumptionAtom);
  const [spatialAggregation] = useAtom(spatialAggregateAtom);
  const inputHandler = (inputEvent: React.ChangeEvent<HTMLInputElement>) => {
    const { target } = inputEvent;

    if (typeof target?.value === 'string') {
      const lowerCase = target.value.toLowerCase();
      setSearchTerm(lowerCase);
    }
  };

  const { data } = useGetState();
  const rankedList = getRankedState(
    data,
    getCo2colorScale,
    'asc',
    selectedDatetime.datetimeString,
    electricityMode,
    spatialAggregation
  );
  const filteredList = rankedList.filter((zone) => {
    if (zone.countryName?.toLowerCase().includes(searchTerm)) {
      return true;
    }
    if (zone.zoneName?.toLowerCase().includes(searchTerm)) {
      return true;
    }
    return false;
  });

  return (
    <div className="flex max-h-[calc(100vh_-_230px)] flex-col py-5 pl-5 pr-1 ">
      <div className="pb-5">
        <div className="font-poppins text-lg font-medium">{t('ranking-panel.title')}</div>
        <div className="text-sm">{t('ranking-panel.subtitle')}</div>
      </div>

      <SearchBar
        placeholder={t('ranking-panel.search')}
        searchHandler={inputHandler}
        value={searchTerm}
      />
      <VirtualizedZoneList data={filteredList} />
      <div className="space-y-4 p-2">
        <RankingPanelAccordion />
        <HorizontalDivider />
        <SocialIconRow />
      </div>
    </div>
  );
}
