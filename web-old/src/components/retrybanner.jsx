import React from 'react';
import { useParams } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { useFeatureToggle } from '../hooks/router';
import { useTranslation } from '../helpers/translation';
import { GRID_DATA_FETCH_REQUESTED, ZONE_HISTORY_FETCH_REQUESTED } from '../helpers/redux';

export const RetryBanner = ({ failedRequestType }) => {
  const { zoneId } = useParams();
  const { __ } = useTranslation();
  const features = useFeatureToggle();
  const dispatch = useDispatch();

  const selectedTimeAggregate = useSelector((state) => state.application.selectedTimeAggregate);
  return (
    <div
      id="connection-warning"
      className={`flash-message ${failedRequestType ? 'active' : ''} ${
        failedRequestType === 'zone' && failedRequestType
      }`}
    >
      <div className="inner">
        {__('misc.oops')}{' '}
        <button
          type="button"
          onClick={(e) => {
            if (failedRequestType === 'grid') {
              dispatch(GRID_DATA_FETCH_REQUESTED({ features, selectedTimeAggregate }));
            }
            if (failedRequestType === 'zone') {
              dispatch(ZONE_HISTORY_FETCH_REQUESTED({ zoneId, features, selectedTimeAggregate }));
            }
            e.preventDefault();
          }}
        >
          {__('misc.retrynow')}
        </button>
        .
      </div>
    </div>
  );
};
