import React, { useState } from 'react';
import { findIndex, isEmpty } from 'lodash';
import styled, { css } from 'styled-components';

const ToggleContainer = styled.div`
  border: none;
  outline: none;
  box-sizing: border-box;
  cursor: pointer;
  box-shadow: 0px 0px 10px 0px rgba(0,0,0,0.15);
  height: 36px;
  transition: all 0.4s;
  display: flex;
  justify-content: flex-end;
  align-content: center;
  background-color: #efefef;
  border-radius: 18px;
  transition: box-shadow 0.4s;

  &:hover {
    box-shadow: 2px 0px 20px 0px rgba(0,0,0,0.25);
  }
`;

const Options = styled.div`
  background: #efefef;
  border-radius: 14px;
  box-shadow: inset 0 1px 4px 0 rgba(0, 0, 0, 0.10);
  display: flex;
  height: 28px;
  flex-direction: row;
  justify-content: flex-end;
  align-content: center;
  align-self: center;
  margin: 0 8px 0 4px;
`;

const Item = styled.div`
  border-radius: 14px 4px 4px 14px;
  font-size: 14px;
  line-height: 28px;
  padding: 0 12px;
  transition: all 0.4s;
  z-index: 9;

  ${props => props.active && css`
    background: #ffffff;
    height: 28px;
    box-shadow: 0px 0px 4px 0px rgba(0,0,0,0.15);
    z-index: 8;
    border-radius: 14px;
  `}
`;

const InfoButton = styled.div`
  height: 28px; 
  width: 28px;
  border-radius: 18px;
  background: #ffffff;
  display: flex;
  justify-content: center;
  align-content: center;
  align-self: center;
  margin: 0 4px;
  box-shadow: 0px 0px 2px 0px rgba(0,0,0,0.1);
  font-weight: bold;
  line-height: 28px;
  transition: all 0.4s;

  &:hover {
    box-shadow: 0px 0px 4px 0px rgba(0,0,0,0.2);
  }
`;

const TooltipContainer = styled.div`
  position: absolute;
  left: -168px;
  width: 150px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  top: 4px;
  transition: opacity 0.4s, visibility 0.4s, transform 0.4s;

  /* Position */
  left: 4px;
  width: 204px;
  top: 49px;

  ${props => (props.visible ? css`
    opacity: 1;
    transform: translateX(0px);
    visibility: visible;
  ` : css`
    opacity: 0;
    transform: translateX(10px);
    visibility: hidden;
  `)}
`;

const TooltipContent = styled.div`
  color: black;
  background-color: #efefef;
  border-radius: 4px;
  text-align: center;
  font-size: 0.9rem;
  padding: 5px 10px;
  box-shadow: 0px 0px 10px 0px rgba(0,0,0,0.15);
`;

const Toggle = ({
  className,
  infoHTML,
  onChange,
  options,
  value,
}) => {
  const [tooltipVisible, setTooltipVisible] = useState(false);

  const activeIndex = findIndex(options, { value });
  const nextIndex = (activeIndex + 1) % options.length;
  const nextValue = options[nextIndex].value;

  return (
    <ToggleContainer className={className}>
      <Options onClick={() => onChange(nextValue)}>
        {options.map(o => (
          <Item key={o.value} active={o.value === value}>
            {o.label}
          </Item>
        ))}
      </Options>
      {!isEmpty(infoHTML) && (
        <React.Fragment>
          <InfoButton onClick={() => setTooltipVisible(!tooltipVisible)}>i</InfoButton>
          <TooltipContainer visible={tooltipVisible}>
            <TooltipContent dangerouslySetInnerHTML={{ __html: infoHTML }} />
          </TooltipContainer>
        </React.Fragment>
      )}
    </ToggleContainer>
  );
};

export default Toggle;
