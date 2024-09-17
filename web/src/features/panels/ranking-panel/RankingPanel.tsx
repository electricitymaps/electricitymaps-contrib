import useGetState from 'api/getState';
import { HorizontalDivider } from 'components/Divider';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { ReactElement, useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Mode } from 'utils/constants';
import {
  isConsumptionAtom,
  selectedDatetimeStringAtom,
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
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const [searchTerm, setSearchTerm] = useState('');
  const isConsumption = useAtomValue(isConsumptionAtom);
  const spatialAggregation = useAtomValue(spatialAggregateAtom);
  const inputHandler = useCallback((inputEvent: React.ChangeEvent<HTMLInputElement>) => {
    const { target } = inputEvent;

    if (typeof target?.value === 'string') {
      const lowerCase = target.value.toLowerCase();
      setSearchTerm(lowerCase);
    }
  }, []);

  const { data } = useGetState();
  const rankedList = getRankedState(
    data,
    getCo2colorScale,
    'asc',
    selectedDatetimeString,
    isConsumption,
    spatialAggregation
  );

  const filteredList = rankedList.filter(
    (zone) =>
      zone.countryName?.toLowerCase().includes(searchTerm) ||
      zone.zoneName?.toLowerCase().includes(searchTerm) ||
      zone.zoneId.toLowerCase().includes(searchTerm)
  );

  return (
    <div className="flex max-h-[calc(100vh-236px)] flex-col py-3 pl-4 pr-1 ">
      <div className="pb-5">
        <h1>{t('ranking-panel.title')}</h1>
        <h2 className="text-sm">{t('ranking-panel.subtitle')}</h2>
      </div>

      <SearchBar
        placeholder={t('ranking-panel.search')}
        searchHandler={inputHandler}
        value={searchTerm}
      />
      <VirtualizedZoneList data={filteredList} />
      {/* TODO: Revise the margin here once the scrollbars are fixed */}
      <div className="my-2 pr-3">
        <RankingPanelAccordion />
        <HorizontalDivider />
        <SocialIconRow />
      </div>
    </div>
  );
}
