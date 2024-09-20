import useGetState from 'api/getState';
import { HorizontalDivider } from 'components/Divider';
import { useCo2ColorScale } from 'hooks/theme';
import { useGetCanonicalUrl } from 'hooks/useGetCanonicalUrl';
import { useAtomValue } from 'jotai';
import { ReactElement, useCallback, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import { metaTitleSuffix, Mode } from 'utils/constants';
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
  const isConsumption = electricityMode === Mode.CONSUMPTION;
  const spatialAggregation = useAtomValue(spatialAggregateAtom);
  const canonicalUrl = useGetCanonicalUrl();
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
    <div className="flex max-h-full flex-col p-2">
      <Helmet prioritizeSeoTags>
        <title>{t('misc.maintitle') + metaTitleSuffix}</title>
        <link rel="canonical" href={canonicalUrl} />
      </Helmet>
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
