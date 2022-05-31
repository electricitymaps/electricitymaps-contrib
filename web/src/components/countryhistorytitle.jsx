import { useSelector } from 'react-redux';
import styled from 'styled-components';
import { useTranslation } from '../helpers/translation';
import React from 'react';
import { formatTimeRange } from '../helpers/formatting';

const Text = styled.span`
  font-size: 1.1em;
`;

export const CountryHistoryTitle = ({ translationKey }) => {
  const { __, i18n } = useTranslation();
  const aggregation = useSelector((state) => state.application.selectedTimeAggregate);
  const localExists = i18n.exists(`${translationKey}.${aggregation}`, { fallbackLng: i18n.language });
  const localDefaultExists = i18n.exists(`${translationKey}.default`, { fallbackLng: i18n.language });
  /*
  Use local for aggregation if exists, otherwise use local default if exists. If no translation exists, use english
  */
  return (
    <Text>
      {localExists
        ? __(`${translationKey}.${aggregation}`)
        : __(`${translationKey}.default`, formatTimeRange(localDefaultExists ? i18n.language : 'en', aggregation))}
    </Text>
  );
};
