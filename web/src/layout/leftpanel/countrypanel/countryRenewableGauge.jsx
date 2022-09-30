/* eslint-disable*/
import React from 'react';
import { useSelector } from 'react-redux';
import CircularGauge from '../../../components/circulargauge';
import { useCurrentZoneData } from '../../../hooks/redux';

export const CountryRenewableGauge = (props) => {
  const electricityMixMode = useSelector((state) => state.application.electricityMixMode);

  const d = useCurrentZoneData();
  if (!d) {
    return <CircularGauge {...props} />;
  }

  const renewableRatio = electricityMixMode === 'consumption' ? d.renewableRatio : d.renewableRatioProduction;
  const countryRenewablePercentage = renewableRatio !== null ? renewableRatio * 100 : null;

  return <CircularGauge percentage={countryRenewablePercentage} {...props} />;
};
