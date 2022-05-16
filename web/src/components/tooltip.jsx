import React from 'react';
import { Portal } from 'react-portal';
import { useSelector } from 'react-redux';
import styled from 'styled-components';

import { useRefWidthHeightObserver } from '../hooks/viewport';

const MARGIN = 16;

const FadedOverlay = styled.div`
  background: rgba(0, 0, 0, 0.25);
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
`;

const Tooltip = ({ id, children, position, onClose }) => {
  const isMobile = useSelector((state) => state.application.isMobile);

  const { ref, width, height } = useRefWidthHeightObserver();

  const screenWidth = window.innerWidth;
  const screenHeight = window.innerHeight;

  if (!position) {
    return null;
  }

  // Note: at first render, width and height will be undefined
  // They will only be set once the DOM node has been created
  const hasDimensions = width > 0 && height > 0;

  const style = {};
  if (hasDimensions) {
    let x = 0;
    let y = 0;
    // Check that tooltip is not larger than screen
    // and that it does overflow on one of the sides
    if (
      2 * MARGIN + width >= screenWidth ||
      (position.x + width + MARGIN >= screenWidth && position.x - width - MARGIN <= 0)
    ) {
      // TODO(olc): Once the tooltip has taken 100% width, it's width will always be 100%
      // as we base our decision to revert based on the current width
      style.width = '100%';
    } else {
      x = position.x + MARGIN;
      // Check that tooltip does not go over the right bound
      if (width + x >= screenWidth) {
        // Put it on the left side
        x = position.x - width - MARGIN;
      }
    }
    y = position.y - MARGIN - height;
    if (y < 0) {
      y = position.y + MARGIN;
    }
    if (y + height + MARGIN >= screenHeight) {
      y = position.y - height - MARGIN;
    }

    style.transform = `translate(${x}px,${y}px)`;
  }

  // Don't show the tooltip until its dimensions have
  // been set and its position correctly calculated.
  style.opacity = hasDimensions ? 1 : 0;

  return (
    <Portal>
      {/*
        Show the faded overlay only on mobile - close the tooltip in
        the next rendering cycle when clicked anywhere on the overlay.
      */}
      {isMobile && <FadedOverlay onClick={() => setTimeout(onClose, 0)} />}
      <div id={id} className="tooltip panel" style={style} ref={ref}>
        {children}
      </div>
    </Portal>
  );
};

export default Tooltip;
