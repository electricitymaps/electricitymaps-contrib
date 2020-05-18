import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import styled from 'styled-components';
import { isEmpty, noop } from 'lodash';

const Wrapper = styled.div`
  position: relative;
`;

const Button = styled.button`
  background-color: #FFFFFF;
  background-image: ${props => (props.active
    ? `url(../images/${props.icon}_active.svg)`
    : `url(../images/${props.icon}.svg)`)};
`;

const ButtonToggle = ({
  active,
  icon,
  onChange,
  tooltip,
}) => {
  const isMobile = useSelector(state => state.application.isMobile);

  const [tooltipVisible, setTooltipVisible] = useState(false);
  const showTooltip = () => { setTooltipVisible(true); };
  const hideTooltip = () => { setTooltipVisible(false); };

  return (
    <Wrapper>
      <Button
        type="button"
        className="layer-button"
        onFocus={isMobile ? noop : showTooltip}
        onMouseOver={isMobile ? noop : showTooltip}
        onMouseOut={isMobile ? noop : hideTooltip}
        onBlur={isMobile ? noop : hideTooltip}
        onClick={onChange}
        active={active}
        icon={icon}
      />
      {tooltipVisible && !isEmpty(tooltip) && (
        <div className="layer-button-tooltip">
          <div className="tooltip-container">
            <div className="tooltip-text">{tooltip}</div>
            <div className="arrow" />
          </div>
        </div>
      )}
    </Wrapper>
  );
};

export default ButtonToggle;
