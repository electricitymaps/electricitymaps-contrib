import styled from 'styled-components';
import React from 'react';
import { BottomSheet } from 'react-spring-bottom-sheet';
import TimeSliderHeader from '../components/timesliderheader';

// Arbitrary value based on Iphone SE at 375 and Iphone 12 Pro at 390
const LARGE_DEVICE_VIEWPORT_WIDTH = 390;

const StyledBottomSheet = styled(BottomSheet)`
  [data-rsbs-header] {
    // override standard styling. Issue in Cordova IOS app
    padding-top: 20px;
    padding-bottom: ${(props) => props.isLargeDevice && '13px'};
    &:before {
      top: 8px;
    }
  }
  [data-rsbs-overlay] {
    padding-bottom: env(safe-area-inset-bottom, 0px);
    padding-bottom: constant(safe-area-inset-bottom, 0px);
    z-index: ${(props) => (props.behind ? 0 : 5)};
  }
  [data-rsbs-scroll] {
    // Disables scrolling, as we want users to open the sheet instead of scrolling inside it
    overflow: hidden;
  }
`;
const isLargeDevice = window.screen.width >= LARGE_DEVICE_VIEWPORT_WIDTH;

// Provide extra swipe up space for larger IOS devices
const snapPoints = isLargeDevice ? [70, 180] : [60, 160];

const ResponsiveSheet = ({ children, visible }) => {
  return (
    <StyledBottomSheet
      scrollLocking={false} // Ensures scrolling is not blocked on IOS
      open={visible}
      snapPoints={() => snapPoints}
      blocking={false}
      header={<TimeSliderHeader />}
      isLargeDevice={isLargeDevice}
    >
      {children}
    </StyledBottomSheet>
  );
};

export default ResponsiveSheet;
