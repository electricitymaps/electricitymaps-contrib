import useGetState from 'api/getState';
import { useCo2ColorScale } from 'hooks/theme';
import { useAtom } from 'jotai';
import { ReactElement, useState } from 'react';
import { selectedDatetimeIndexAtom, productionConsumptionAtom, timeAverageAtom } from 'utils/state/atoms';
import { useTranslation } from '../../../translation/translation';
import { getRankedState } from './getRankingPanelData';
import SearchBar from './SearchBar';
import ZoneList from './ZoneList';

export default function RankingPanel(): ReactElement {
  const { __ } = useTranslation();
  const getCo2colorScale = useCo2ColorScale();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [searchTerm, setSearchTerm] = useState('');
  const [electricityMode] = useAtom(productionConsumptionAtom);
  const inputHandler = (inputEvent: any) => {
    const lowerCase = inputEvent.target.value.toLowerCase();
    setSearchTerm(lowerCase);
  };

  const { isLoading, isSuccess, isError, error, data } = useGetState();
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
    <div className="p-5">
      <div className="pb-5">
        <div className="title poppins text-lg font-medium">
          {__('left-panel.zone-list-header-title')}
        </div>
        <div className="subtitle inter text-xs">
          {__('left-panel.zone-list-header-subtitle')}
        </div>
      </div>

      <SearchBar
        placeholder={__('left-panel.search')}
        searchHandler={inputHandler}
        value={searchTerm}
      />
      {!isLoading && <ZoneList data={filteredList} />}
      {/* <InfoText /> TODO */}
    </div>
  );
}
