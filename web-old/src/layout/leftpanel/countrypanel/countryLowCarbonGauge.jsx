import React from 'react';
import { useSelector } from 'react-redux';
import CircularGauge from '../../../components/circulargauge';
import { useCurrentZoneData } from '../../../hooks/redux';

export const CountryLowCarbonGauge = (props) => {
  const electricityMixMode = useSelector((state) => state.application.electricityMixMode);

  const d = useCurrentZoneData();
  if (!d) {
    return <CircularGauge {...props} />;
  }

  const fossilFuelRatio = electricityMixMode === 'consumption' ? d.fossilFuelRatio : d.fossilFuelRatioProduction;
  const countryLowCarbonPercentage = fossilFuelRatio !== null ? 100 - fossilFuelRatio * 100 : null;

  return <CircularGauge percentage={countryLowCarbonPercentage} {...props} />;
};
