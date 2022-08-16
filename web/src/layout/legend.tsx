import React from 'react';
import { connect } from 'react-redux';
import styled, { css } from 'styled-components';

import { dispatchApplication } from '../store';
import { useTranslation } from '../helpers/translation';

import HorizontalColorbar from '../components/horizontalcolorbar';
import Icon from '../components/icon';
import { solarColor, windColor } from '../helpers/scales';
import { useSolarEnabled, useWindEnabled } from '../hooks/router';
import { useCo2ColorScale } from '../hooks/theme';

const LegendsContainer = styled.div`
  position: absolute;
  bottom: 0px;
  right: 0px;
  float: left;
  background-color: #fafafa;
  border-radius: 6px;
  padding: 12px 10px 10px 10px;
  margin: 16px;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
  z-index: 99;
  transition: width 0.4s, height 0.4s;
  font-family: 'Euclid Triangle', 'Open Sans', sans-serif;
  font-size: 0.8rem;
  user-select: none;

  @media (max-width: 767px) {
    display: none;
  }

  // Apply specific styles if the legend is collapsed
  ${(props) =>
    (props as any).isCollapsed &&
    css`
      width: 90px;
      height: 18px;
      padding: 6px 10px 10px;
    `}

  div {
    padding: 2px 6px 5px 6px;
  }
`;

const LegendItemWrapper = styled.div`
  width: 15em;
  padding-top: 7px;
`;

const ToggleLegendButton = styled.i`
  font-size: 24px;
  position: absolute;
  right: 5px;
  top: 5px;
  &:hover {
    cursor: pointer;
  }
`;

const StyledMobileHeader = styled.div`
  text-align: ${(props) => ((props as any).isCollapsed ? 'left' : 'center')};
  font-weight: bold;
  margin-bottom: 5px;

  @media (min-width: 768px) {
    display: none;
    text-align: center;
  }
}`;

const MobileHeader = ({ onToggle, isOpen, label }: any) => (
  // @ts-expect-error TS(2769): No overload matches this call.
  <StyledMobileHeader isCollapsed={!isOpen}>
    <span>{label}</span>
    <ToggleLegendButton onClick={onToggle}>
      {/* @ts-expect-error TS(2322): Type '{ iconName: string; }' is not assignable to ... Remove this comment to see the full error message */}
      <Icon iconName={isOpen ? 'call_received' : 'call_made'} />
    </ToggleLegendButton>
  </StyledMobileHeader>
);

const LegendItem = ({ isEnabled, label, unit, children }: any) =>
  !isEnabled ? null : (
    <LegendItemWrapper>
      <div>
        {label} <small>({unit})</small>
      </div>
      {children}
    </LegendItemWrapper>
  );

const mapStateToProps = (state: any) => ({
  co2ColorbarValue: state.application.co2ColorbarValue,
  legendVisible: state.application.legendVisible,
  solarColorbarValue: state.application.solarColorbarValue,
  windColorbarValue: state.application.windColorbarValue,
});

const Legend = ({ co2ColorbarValue, legendVisible, solarColorbarValue, windColorbarValue }: any) => {
  const { __ } = useTranslation();
  const co2ColorScale = useCo2ColorScale();
  const solarEnabled = useSolarEnabled();
  const windEnabled = useWindEnabled();

  const toggleLegend = () => {
    dispatchApplication('legendVisible', !legendVisible);
  };

  return (
    // @ts-expect-error TS(2769): No overload matches this call.
    <LegendsContainer isCollapsed={!legendVisible}>
      <MobileHeader label={__('misc.legend')} onToggle={toggleLegend} isOpen={legendVisible} />
      {legendVisible && (
        <React.Fragment>
          <LegendItem label={__('legends.windpotential')} unit="m/s" isEnabled={windEnabled}>
            <HorizontalColorbar
              id="wind-potential-bar"
              colorScale={windColor}
              currentValue={windColorbarValue}
              markerColor="black"
              ticksCount={6}
            />
          </LegendItem>
          <LegendItem
            label={__('legends.solarpotential')}
            unit={
              <span>
                W/m<span className="sup">2</span>
              </span>
            }
            isEnabled={solarEnabled}
          >
            <HorizontalColorbar
              id="solar-potential-bar"
              colorScale={solarColor}
              currentValue={solarColorbarValue}
              markerColor="red"
              ticksCount={5}
            />
          </LegendItem>
          <LegendItem label={__('legends.carbonintensity')} unit="gCO₂eq/kWh" isEnabled>
            <HorizontalColorbar
              id="co2intensity-bar"
              colorScale={co2ColorScale}
              currentValue={co2ColorbarValue}
              markerColor="white"
              ticksCount={5}
            />
          </LegendItem>
        </React.Fragment>
      )}
    </LegendsContainer>
  );
};

export default connect(mapStateToProps)(Legend);
