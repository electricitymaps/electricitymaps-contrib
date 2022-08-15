import React from 'react';
import styled from 'styled-components';
import { noop } from '../helpers/noop';

import Tooltip from './tooltip';
import Icon from './icon';

const DisclaimerIcon = styled.span`
  font-size: 20px;
  cursor: help;
  height: 20px;
  color: rgba(0, 0, 0, 0.35);
  margin-top: 4px;
`;

const TooltipInner = styled.div`
  max-width: 200px;
  font-size: smaller;
`;

const DisclaimerTooltip = ({ onClose, text, position }) => (
  <Tooltip id="disclaimer-info-tooltip" position={{ x: position.clientX, y: position.clientY }} onClose={onClose}>
    <TooltipInner>{text}</TooltipInner>
  </Tooltip>
);

const CountryDisclaimer = ({ text, isMobile }) => {
  const [tooltip, setTooltip] = React.useState(null);
  return (
    <React.Fragment>
      <DisclaimerIcon
        onClick={isMobile ? ({ clientX, clientY }) => setTooltip({ clientX, clientY }) : noop}
        onMouseMove={!isMobile ? ({ clientX, clientY }) => setTooltip({ clientX, clientY }) : noop}
        onMouseOut={() => setTooltip(null)}
        onBlur={() => setTooltip(null)}
      >
        <Icon iconName="error" />
      </DisclaimerIcon>
      {tooltip && <DisclaimerTooltip text={text} position={tooltip} />}
    </React.Fragment>
  );
};

export default CountryDisclaimer;
