import GlassContainer from 'components/GlassContainer';
import { useGetCanonicalUrl } from 'hooks/useGetCanonicalUrl';
import { ReactElement, useCallback, useEffect, useMemo, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import { twMerge } from 'tailwind-merge';
import { metaTitleSuffix } from 'utils/constants';

import {
  getAllZones,
  getCombinedSearchResults,
  useGetSolarAssetsForSearch,
} from './getSearchData';
import NoResults from './NoResults';
import SearchBar from './SearchBar';
import SearchResultList from './SearchResultList';

export default function SearchPanel(): ReactElement {
  const { t, i18n } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const canonicalUrl = useGetCanonicalUrl();

  // Memoize the zone data to prevent unnecessary recalculations
  const zoneData = useMemo(() => getAllZones(i18n.language), [i18n.language]);

  // Get solar assets data for search
  const { solarAssets, isLoading: isLoadingSolarAssets } = useGetSolarAssetsForSearch();

  const inputHandler = useCallback((inputEvent: React.ChangeEvent<HTMLInputElement>) => {
    const { target } = inputEvent;

    if (typeof target?.value === 'string') {
      const lowerCase = target.value.toLowerCase();
      setSearchTerm(lowerCase);
    }
  }, []);

  // Memoize the filtered list to prevent unnecessary recalculations
  const combinedResults = useMemo(
    () => getCombinedSearchResults(searchTerm, zoneData, solarAssets),
    [searchTerm, zoneData, solarAssets]
  );

  // Update selected index when filtered list changes
  useEffect(() => {
    setSelectedIndex(combinedResults.length > 0 ? 0 : -1);
  }, [combinedResults]);

  return (
    <GlassContainer
      className={twMerge(
        `pointer-events-auto left-3 top-3 transition-all has-[:focus]:bg-white/90 has-[:focus]:shadow-[0_0_0_2px_rgba(0,0,0,0.05)]`,
        searchTerm && 'sm:bg-white/90 sm:dark:bg-neutral-900/90'
      )}
    >
      <Helmet prioritizeSeoTags>
        <title>{t('misc.maintitle') + metaTitleSuffix}</title>
        <link rel="canonical" href={canonicalUrl} />
      </Helmet>

      <div className="flex flex-grow flex-col">
        <SearchBar
          placeholder={t('ranking-panel.search')}
          searchHandler={inputHandler}
          value={searchTerm}
          selectedIndex={selectedIndex}
          onSelectedIndexChange={setSelectedIndex}
          totalResults={combinedResults.length}
        />

        <div
          className={twMerge(
            'flex-grow border-t border-transparent transition-all',
            searchTerm && 'border-neutral-200/60 dark:border-neutral-700/60'
          )}
        >
          {searchTerm &&
            combinedResults.length === 0 &&
            (isLoadingSolarAssets ? (
              <div className="flex h-full items-center justify-center p-4 text-sm text-neutral-500">
                {t('loading')}...
              </div>
            ) : (
              <NoResults />
            ))}
          <SearchResultList data={combinedResults} selectedIndex={selectedIndex} />
        </div>
      </div>
    </GlassContainer>
  );
}
