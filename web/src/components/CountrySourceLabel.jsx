import React from 'react';
import styled from 'styled-components';
import Tooltip from './tooltip';
import { useTranslation } from '../helpers/translation';
import { noop } from '../helpers/noop';
import Icon from './icon';

const SourceLabelContainer = styled.span`
    border-radius: 0.25rem;
    background-color: lightblue;
    color: rgb(76, 76, 76);
    font-weight: bold;
    padding: 0.2rem;
    font-size: 0.8em;
    margin-left: 0.4em;
    line-height: 0.8em;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    &:hover {
      cursor: help;
    }
    & svg {
      height: 16px;
      width: 16px;
      margin-right: 0.2em;
    }
  `;

  const TooltipInner = styled.div`
    max-width: 180px;
    font-size: smaller;
  `;
const SourceLabel = ({ isMobile, isDataEstimated }) => {




  const [tooltip, setTooltip] = React.useState(null);
  const { __ } = useTranslation();

  const TooltipComponent = tooltip && (
    <Tooltip id="estimated-info-tooltip" position={{ x: tooltip.clientX, y: tooltip.clientY }}>
      <TooltipInner>{isDataEstimated ? __('country-panel.estimatedTooltip') : 'API data'}</TooltipInner>
    </Tooltip>
  );

  return (
    <React.Fragment>
      <SourceLabelContainer
        onClick={isMobile ? ({ clientX, clientY }) => setTooltip({ clientX, clientY }) : noop}
        onMouseMove={!isMobile ? ({ clientX, clientY }) => setTooltip({ clientX, clientY }) : noop}
        onMouseOut={() => setTooltip(null)}
        onBlur={() => setTooltip(null)}
        style={{ background: isDataEstimated ? '#FFD700' : '#78cde8' }}
      >
        <Icon iconName={isDataEstimated ? 'insights' : 'api'} />{' '}
        {isDataEstimated ? __('country-panel.estimated') : 'API'}
      </SourceLabelContainer>
      {TooltipComponent}
    </React.Fragment>
  );
};

export default SourceLabel;
