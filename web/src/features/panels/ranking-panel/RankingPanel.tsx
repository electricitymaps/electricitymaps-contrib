import useGetState from 'api/getState';
import { HorizontalDivider } from 'components/Divider';
import { useGetCanonicalLink } from 'hooks/getCanonicalLink';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { ReactElement, useCallback, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import {
  productionConsumptionAtom,
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
  const electricityMode = useAtomValue(productionConsumptionAtom);
  const spatialAggregation = useAtomValue(spatialAggregateAtom);
  const inputHandler = useCallback((inputEvent: React.ChangeEvent<HTMLInputElement>) => {
    const { target } = inputEvent;

    if (typeof target?.value === 'string') {
      const lowerCase = target.value.toLowerCase();
      setSearchTerm(lowerCase);
    }
  }, []);

  const { data } = useGetState();

  const canonicalLink = useGetCanonicalLink();
  const rankedList = getRankedState(
    data,
    getCo2colorScale,
    'asc',
    selectedDatetimeString,
    electricityMode,
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
      <Helmet prioritizeSeoTags>{canonicalLink}</Helmet>
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
      {/* TODO: Revise the margin here once the scrollbars are fixed */}
      <div className="my-2 pr-3">
        <RankingPanelAccordion />
        <HorizontalDivider />
        <SocialIconRow />
      </div>
    </div>
  );
}
