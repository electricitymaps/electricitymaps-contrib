import React from 'react';
import styled from 'styled-components';
import Tooltip from './tooltip';
import { __ } from '../helpers/translation';
import { noop } from 'lodash';

const EstimationLabel = styled.div`
  background: #FFD700;
  color: #000;
  display: inline-block;
  padding: 0 4px;
  margin-left: 4px;
  border-radius: 4px;
`;

const TooltipInner = styled.div`
  max-width: 200px;
  font-size: smaller;
`;

const EstimatedLabel = ({ isMobile }) => {
  const [tooltip, setTooltip] = React.useState(null);

  const TooltipComponent = tooltip && (
    <Tooltip
      id="estimated-info-tooltip"
      position={{ x: tooltip.clientX, y: tooltip.clientY }}
    >
      <TooltipInner>{__('country-panel.estimatedTooltip')}</TooltipInner>
    </Tooltip>
  );

  return (
    <React.Fragment>
      <EstimationLabel
        onClick={isMobile ? ({ clientX, clientY }) => setTooltip({ clientX, clientY }) : noop}
        onMouseMove={!isMobile ? ({ clientX, clientY }) => setTooltip({ clientX, clientY }) : noop}
        onMouseOut={() => setTooltip(null)}
        onBlur={() => setTooltip(null)}
      >
        {__('country-panel.estimated')}
      </EstimationLabel>
      {TooltipComponent}
    </React.Fragment>
  );
};

export default EstimatedLabel;

