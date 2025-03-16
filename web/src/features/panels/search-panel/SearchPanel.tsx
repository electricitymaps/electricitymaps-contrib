import GlassContainer from 'components/GlassContainer';
import { useGetCanonicalUrl } from 'hooks/useGetCanonicalUrl';
import { ReactElement, useCallback, useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';
import { twMerge } from 'tailwind-merge';
import { metaTitleSuffix } from 'utils/constants';

import { getAllZones, getFilteredList } from './getSearchData';
import NoResults from './NoResults';
import SearchBar from './SearchBar';
import { VirtualizedZoneList } from './ZoneList';

export default function SearchPanel(): ReactElement {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const canonicalUrl = useGetCanonicalUrl();

  const inputHandler = useCallback((inputEvent: React.ChangeEvent<HTMLInputElement>) => {
    const { target } = inputEvent;

    if (typeof target?.value === 'string') {
      const lowerCase = target.value.toLowerCase();
      setSearchTerm(lowerCase);
    }
  }, []);

  const zoneData = getAllZones();
  const filteredList = getFilteredList(searchTerm, zoneData);

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
        />

        <div
          className={twMerge(
            'flex-grow border-t border-transparent transition-all',
            searchTerm && 'border-neutral-200/60 dark:border-neutral-700/60'
          )}
        >
          {searchTerm && filteredList.length === 0 && <NoResults />}
          <VirtualizedZoneList data={filteredList} />
        </div>
      </div>
    </GlassContainer>
  );
}
