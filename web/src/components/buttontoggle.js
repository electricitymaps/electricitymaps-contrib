import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import styled from 'styled-components';
import { isEmpty, noop } from 'lodash';

const Wrapper = styled.div`
  position: relative;
`;

const Button = styled.button`
  border-radius: 6px;
  width: 35px;
  height: 35px;
  margin-bottom: 10px;
  background-repeat: no-repeat;
  background-position: center;
  background-size: 58% 57%;
  border: none;
  outline: none;
  box-sizing: border-box;
  cursor: pointer;
  transition: all 0.4s;
  box-shadow: 0px 0px 10px 0px ${({ theme }) => theme.shadowColor};
  background-color: ${({ theme }) => theme.background};
  background-image: url(${(props) =>
    props.active
      ? resolvePath(`images/${props.icon}_active.svg`)
      : resolvePath(`images/${props.icon}.svg`)});
  &:hover {
    background-color: ${({ theme }) => theme.lightBackground};
    box-shadow: 2px 0px 20px 0px ${({ theme }) => theme.shadowColorHovered};
  }
`;

const ButtonTooltip = styled.div`
  position: absolute;
  left: -168px;
  width: 150px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  top: 4px;
  visibility: visible;
  opacity: 1;
  transform: translateX(0px);
  transition: opacity 0.4s, visibility 0.4s, transform 0.4s;
`;

const TooltipContainer = styled.div`
  display: flex;
  align-items: center;
`;

const TooltipText = styled.div`
  background-color: ${({ theme }) => theme.background};
  color: ${({ theme }) => theme.text};
  border-radius: 4px;
  text-align: center;
  font-size: 0.9rem;
  padding: 5px 10px;
  box-shadow: 0px 0px 10px 0px ${({ theme }) => theme.shadowColor};
`;

const ButtonToggle = ({ active, icon, onChange, tooltip }) => {
  const isMobile = useSelector((state) => state.application.isMobile);

  const [tooltipVisible, setTooltipVisible] = useState(false);
  const showTooltip = () => {
    setTooltipVisible(true);
  };
  const hideTooltip = () => {
    setTooltipVisible(false);
  };

  return (
    <Wrapper>
      <Button
        type="button"
        onFocus={isMobile ? noop : showTooltip}
        onMouseOver={isMobile ? noop : showTooltip}
        onMouseOut={isMobile ? noop : hideTooltip}
        onBlur={isMobile ? noop : hideTooltip}
        onClick={onChange}
        active={active}
        icon={icon}
      />
      {tooltipVisible && !isEmpty(tooltip) && (
        <ButtonTooltip>
          <TooltipContainer>
            <TooltipText>{tooltip}</TooltipText>
          </TooltipContainer>
        </ButtonTooltip>
      )}
    </Wrapper>
  );
};

export default ButtonToggle;
