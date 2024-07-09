import useGetState from 'api/getState';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtomValue } from 'jotai';
import { ReactElement, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  productionConsumptionAtom,
  selectedDatetimeStringAtom,
  spatialAggregateAtom,
} from 'utils/state/atoms';

import { getRankedState } from './getRankingPanelData';
import InfoText from './InfoText';
import SearchBar from './SearchBar';
import SocialButtons from './SocialButtons';
import { VirtualizedZoneList } from './ZoneList';

export default function RankingPanel(): ReactElement {
  const { t } = useTranslation();
  const getCo2colorScale = useCo2ColorScale();
  const selectedDatetimeString = useAtomValue(selectedDatetimeStringAtom);
  const [searchTerm, setSearchTerm] = useState('');
  const electricityMode = useAtomValue(productionConsumptionAtom);
  const spatialAggregation = useAtomValue(spatialAggregateAtom);
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
    selectedDatetimeString,
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
        <div className="font-poppins text-lg font-medium">
          {t('left-panel.zone-list-header-title')}
        </div>
        <div className="text-sm">{t('left-panel.zone-list-header-subtitle')}</div>
      </div>

      <SearchBar
        placeholder={t('left-panel.search')}
        searchHandler={inputHandler}
        value={searchTerm}
      />
      <VirtualizedZoneList data={filteredList} />
      <div className="space-y-4 p-2">
        <InfoText />
        <SocialButtons />
      </div>
    </div>
  );
}
