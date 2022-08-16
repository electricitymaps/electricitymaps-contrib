import React from 'react';
import { useTranslation } from '../helpers/translation';
import styled from 'styled-components';
import { useSelector } from 'react-redux';
import { TimeDisplay } from './timeDisplay';

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
  display: ${(props) => ((props as any).loading ? 'none' : 'flex')};
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
  const { __ } = useTranslation();
  const isLoading = useSelector((state) => (state as any).data.isLoadingGrid);

  return (
    <Wrapper>
      <Title>{__('time-controller.title')}</Title>
      {/* @ts-expect-error TS(2769): No overload matches this call. */}
      <DateDisplay data-test-id="date-display" loading={isLoading}>
        <TimeDisplay />
      </DateDisplay>
    </Wrapper>
  );
};

export default TimeSliderHeader;
