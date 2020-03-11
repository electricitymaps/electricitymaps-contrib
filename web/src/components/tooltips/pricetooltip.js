import React from 'react';
import { connect } from 'react-redux';
import getSymbolFromCurrency from 'currency-symbol-map';

import { PRICES_GRAPH_LAYER_KEY } from '../../helpers/constants';

import TooltipContainer from './tooltipcontainer';

const mapStateToProps = state => ({
  visible: state.application.tooltipDisplayMode === PRICES_GRAPH_LAYER_KEY,
  zoneData: state.application.tooltipZoneData,
});

const PriceTooltip = ({ visible, zoneData }) => {
  if (!visible) return null;

  const priceIsDefined = zoneData.price !== null && zoneData.price.value !== null;
  
  return (
    <TooltipContainer id="price-tooltip">
      <span className="value">
        {priceIsDefined ? zoneData.price.value : '?'}
      </span>
      {' '}
      <span className="currency">
        {priceIsDefined ? getSymbolFromCurrency(zoneData.price.currency) : '?'}
      </span> / MWh
    </TooltipContainer>
  );
};

export default connect(mapStateToProps)(PriceTooltip);
