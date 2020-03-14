import React from 'react';
import { connect } from 'react-redux';
import { isNumber } from 'lodash';

import getSymbolFromCurrency from 'currency-symbol-map';

import { PRICES_GRAPH_LAYER_KEY } from '../../helpers/constants';

import Tooltip from '../tooltip';

const mapStateToProps = state => ({
  visible: state.application.tooltipDisplayMode === PRICES_GRAPH_LAYER_KEY,
  zoneData: state.application.tooltipZoneData,
});

const PriceTooltip = ({ visible, zoneData }) => {
  if (!visible) return null;

  const priceIsDefined = zoneData.price && isNumber(zoneData.price.value);
  const currency = priceIsDefined ? getSymbolFromCurrency(zoneData.price.currency) : '?';
  const value = priceIsDefined ? zoneData.price.value : '?';
  
  return (
    <Tooltip id="price-tooltip">
      {value} {currency} / MWh
    </Tooltip>
  );
};

export default connect(mapStateToProps)(PriceTooltip);
