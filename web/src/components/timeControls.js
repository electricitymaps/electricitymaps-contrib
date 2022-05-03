import React from 'react';

// import { useTranslation } from '../../helpers/translation';
// import Tooltip from '../tooltip';
import styled, { css } from 'styled-components';
import { formatHourlyDate } from '../helpers/formatting';

const Title = styled.span`
  font-size: calc(11px + 0.2vw);
  font-weight: 700;
  white-space: nowrap;
  height: 100%;
  display: flex;
  align-items: center;
`;
const DateRangeOption = styled.span`
  font-size: 0.8rem;
  padding: 8px;
  margin-right: 5px;
  padding-left: 12px;
  padding-right: 12px;
  border-radius: 16px;
  font-weight: ${(props) => (props.selected ? 700 : 500)};
  opacity: ${(props) => (props.selected ? 1 : 0.5)};
  cursor: not-allowed;
  ${(props) =>
    props.selected &&
    css`
      background-color: white;
      box-shadow: 0.1px 0.1px 5px rgba(0, 0, 0, 0.1);
      cursor: pointer;
    `}
`;

const DateDisplay = styled.div`
  display: flex;
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
`;

const DateOptionWrapper = styled.div`
  display: flex;
  justify-content: flex-start;
  padding-top: 8px;
`;

const TimeControls = ({ date }) => {
  return (
    <div>
      <Wrapper>
        <Title>Display data from the last</Title>
        <DateDisplay>{formatHourlyDate(date)}</DateDisplay>
      </Wrapper>
      <DateOptionWrapper>
        <DateRangeOption selected>Day</DateRangeOption>
        <DateRangeOption>Month</DateRangeOption>
        <DateRangeOption>Year</DateRangeOption>
        <DateRangeOption>5 years</DateRangeOption>
      </DateOptionWrapper>
    </div>
  );
};

export default TimeControls;
