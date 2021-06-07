import React, { useState } from 'react';
import { isEmpty } from 'lodash';
import styled, { css } from 'styled-components';

import InfoTooltip from './infotooltip';

const Wrapper = styled.div`
  align-content: center;
  background-color: ${({ theme }) => theme.background};
  border: none;
  border-radius: 18px;
  color: ${({ theme }) => theme.textFaded};
  box-shadow: 0px 0px 10px 0px ${({ theme }) => theme.shadowColor};
  box-sizing: border-box;
  cursor: pointer;
  display: flex;
  height: 36px;
  justify-content: flex-end;
  outline: none;
  transition: all 0.4s;
  user-select: none;
  &:hover {
    box-shadow: 2px 0px 20px 0px ${({ theme }) => theme.shadowColorHovered};
  }
`;

const Options = styled.div`
  align-content: center;
  align-self: center;
  background: ${({ theme }) => theme.shadowColor};
  border-radius: 14px;
  box-shadow: inset 0 1px 4px 0 ${({ theme }) => theme.shadowColor};
  display: flex;
  flex-direction: row;
  height: 28px;
  justify-content: flex-end;
  margin: 0 4px;
`;

const OptionItem = styled.div`
  border-radius: 14px 4px 4px 14px;
  font-size: 14px;
  line-height: 28px;
  padding: 0 12px;
  transition: all 0.4s;
  z-index: 9;
  font-family: 'Euclid Triangle', 'Open Sans', sans-serif;

  ${(props) =>
    props.active &&
    css`
      color: ${({ theme }) => theme.text};
      background: ${({ theme }) => theme.lightBackground};
      border-radius: 14px;
      box-shadow: 0px 0px 4px 0px ${({ theme }) => theme.shadowColor};
      height: 28px;
      z-index: 8;
    `}
`;

const InfoButton = styled.div`
  align-content: center;
  align-self: center;
  background: ${({ theme }) => theme.background};
  border-radius: 18px;
  box-shadow: 0px 0px 2px 0px ${({ theme }) => theme.shadowColor};
  border: 1px solid ${({ theme }) => theme.shadowColor};
  display: flex;
  font-weight: bold;
  height: 28px;
  justify-content: center;
  line-height: 28px;
  margin: 0 4px;
  transition: all 0.4s;
  width: 28px;
  user-select: none;
  &:hover {
    box-shadow: 0px 0px 4px 0px ${({ theme }) => theme.shadowColorHovered};
    background: ${({ theme }) => theme.lightBackground};
  }
`;

export default ({ infoHTML, onChange, options, value }) => {
  const [tooltipVisible, setTooltipVisible] = useState(false);

  return (
    <Wrapper>
      <Options>
        {options.map((o) => (
          <OptionItem key={o.value} active={o.value === value} onClick={() => onChange(o.value)}>
            {o.label}
          </OptionItem>
        ))}
      </Options>
      {!isEmpty(infoHTML) && (
        <React.Fragment>
          <InfoButton onClick={() => setTooltipVisible(!tooltipVisible)}>i</InfoButton>
          <InfoTooltip
            htmlContent={infoHTML}
            style={{ left: 4, width: 204, top: 49 }}
            visible={tooltipVisible}
          />
        </React.Fragment>
      )}
    </Wrapper>
  );
};
