import React from 'react';
import { useTranslation } from '../helpers/translation';
import styled from 'styled-components';
import { formatDate } from '../helpers/formatting';
import { useSelector } from 'react-redux';
import { useCurrentDatetimes } from '../hooks/redux';

const Title = styled.span`
  font-size: calc(11px + 0.2vw);
  font-weight: 700;
  white-space: nowrap;
  height: 100%;
  display: flex;
  align-items: center;
  @media (max-width: 768px) {
    font-size: 13px;
  }
`;

const DateDisplay = styled.div`
  display: ${(props) => (props.loading ? 'none' : 'flex')};
  align-items: center;
  font-size: calc(9px + 0.2vw);
  background-color: #f0f0f0;
  padding-left: 12px;
  padding-right: 12px;
  border-radius: 30px;
  max-width: 300px;
  white-space: nowrap;
  height: 100%;
`;

const Wrapper = styled.div`
  display: flex;
  justify-content: space-between;
  height: 30px;
  @media (max-width: 315px) {
    flex-direction: column-reverse;
    align-items: center;
  }
`;

const TimeSliderHeader = () => {
  const { __, i18n } = useTranslation();
  const selectedTimeAggregate = useSelector((state) => state.application.selectedTimeAggregate);
  const selectedZoneTimeIndex = useSelector((state) => state.application.selectedZoneTimeIndex);
  const isLoading = useSelector((state) => state.data.isLoadingGrid);
  const datetimes = useCurrentDatetimes();

  const timeValue = typeof selectedZoneTimeIndex === 'number' ? datetimes[selectedZoneTimeIndex]?.valueOf() : null;

  // TODO: Do we need the anchored time index here?
  const date = new Date(timeValue);
  return (
    <Wrapper>
      <Title>{__('time-controller.title')}</Title>
      <DateDisplay data-test-id="date-display" loading={isLoading}>
        {formatDate(date, i18n.language, selectedTimeAggregate)}
      </DateDisplay>
    </Wrapper>
  );
};

export default TimeSliderHeader;
