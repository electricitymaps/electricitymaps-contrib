import React from 'react';
import { useTranslation } from '../helpers/translation';
import styled, { css } from 'styled-components';
import { formatHourlyDate } from '../helpers/formatting';

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
const DateRangeOption = styled.span`
  font-size: 0.8rem;
  padding: 8px;
  margin-right: 5px;
  padding-left: 12px;
  padding-right: 12px;
  border-radius: 16px;
  white-space: nowrap;
  cursor: default;
  font-weight: ${(props) => (props.active ? 700 : 500)};
  opacity: ${(props) => (props.active ? 1 : 0.5)};
  ${(props) =>
    props.active &&
    css`
      cursor: pointer;
      background-color: white;
      box-shadow: 0.1px 0.1px 5px rgba(0, 0, 0, 0.1);
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
  @media (max-width: 315px) {
    flex-direction: column-reverse;
    align-items: center;
  }
`;

const DateOptionWrapper = styled.div`
  display: flex;
  justify-content: flex-start;
  padding-top: 8px;
`;

const options = [
  { key: 'day', label: 'time-controller.day' },
  { key: 'month', label: 'time-controller.month' },
  { key: 'year', label: 'time-controller.year' },
  { key: '5year', label: 'time-controller.5year' },
];

const TimeControls = ({ date, selectedTimeAggregate, handleTimeAggregationChange }) => {
  const { __ } = useTranslation();

  return (
    <div>
      <Wrapper>
        <Title>{__('time-controller.title')}</Title>
        <DateDisplay>{formatHourlyDate(date)}</DateDisplay>
      </Wrapper>
      <DateOptionWrapper>
        {options.map((o) => (
          <DateRangeOption
            key={o.key}
            active={o.key === selectedTimeAggregate}
            onClick={() => {
              handleTimeAggregationChange(o.key);
            }}
          >
            {__(o.label)}
          </DateRangeOption>
        ))}
      </DateOptionWrapper>
    </div>
  );
};

export default TimeControls;
