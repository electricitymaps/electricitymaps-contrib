import useGetState from 'api/getState';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { ReactElement, useState } from 'react';
import {
  productionConsumptionAtom,
  selectedDatetimeIndexAtom,
  timeAverageAtom,
} from 'utils/state/atoms';
import { useTranslation } from '../../../translation/translation';
import { getRankedState } from './getRankingPanelData';
import InfoText from './InfoText';
import SearchBar from './SearchBar';
import SocialButtons from './SocialButtons';
import ZoneList from './ZoneList';

export default function RankingPanel(): ReactElement {
  const { __ } = useTranslation();
  const getCo2colorScale = useCo2ColorScale();
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [searchTerm, setSearchTerm] = useState('');
  const [electricityMode] = useAtom(productionConsumptionAtom);
  const inputHandler = (inputEvent: any) => {
    const lowerCase = inputEvent.target.value.toLowerCase();
    setSearchTerm(lowerCase);
  };

  const { data } = useGetState();
  const rankedList = getRankedState(
    data,
    getCo2colorScale,
    'asc',
    selectedDatetime.datetimeString,
    electricityMode
  );
  const filteredList = rankedList.filter((zone) => {
    if (zone.countryName && zone.countryName.toLowerCase().includes(searchTerm)) {
      return true;
    }
    if (zone.zoneName && zone.zoneName.toLowerCase().includes(searchTerm)) {
      return true;
    }
    return false;
  });

  return (
    <div className="flex max-h-[calc(100vh_-_230px)] flex-col py-5 pl-5 pr-1 ">
      <div className="pb-5">
        <div className="font-poppins text-lg font-medium">
          {__('left-panel.zone-list-header-title')}
        </div>
        <div className="text-sm">{__('left-panel.zone-list-header-subtitle')}</div>
      </div>

      <SearchBar
        placeholder={__('left-panel.search')}
        searchHandler={inputHandler}
        value={searchTerm}
      />
      <ZoneList data={filteredList} />
      <div className="space-y-4 p-2">
        <InfoText />
        <SocialButtons />
      </div>
    </div>
  );
}
