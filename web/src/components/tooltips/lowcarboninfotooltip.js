import React from 'react';
import { connect } from 'react-redux';

import { __ } from '../../helpers/translation';
import { LOW_CARBON_INFO_TOOLTIP_KEY } from '../../helpers/constants';

import TooltipContainer from './tooltipcontainer';

const mapStateToProps = state => ({
  visible: state.application.tooltipDisplayMode === LOW_CARBON_INFO_TOOLTIP_KEY,
});

const LowCarbonInfoTooltip = ({ visible }) => {
  if (!visible) return null;

  return (
    <TooltipContainer id="lowcarb-info-tooltip">
      <b><span id="lowcarb-info-title">{__('tooltips.lowcarbon')}</span></b>
      <br />
      <small><span id="lowcarb-info-text">{__('tooltips.lowCarbDescription')}</span></small>
      <br />
    </TooltipContainer>
  );
};

export default connect(mapStateToProps)(LowCarbonInfoTooltip);
