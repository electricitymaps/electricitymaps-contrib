import React, { useRef } from 'react';
import { connect } from 'react-redux';

import { useWidthObserver, useHeightObserver } from '../../effects';

const MARGIN = 16;

const mapStateToProps = state => ({
  position: state.application.tooltipPosition,
});

const TooltipContainer = ({ id, children, position }) => {
  const ref = useRef(null);

  const width = useWidthObserver(ref);
  const height = useHeightObserver(ref);

  const screenWidth = window.innerWidth;
  const screenHeight = window.innerHeight;

  if (!position) return null;

  const style = {};
  let x = 0;
  let y = 0;
  // Check that tooltip is not larger than screen
  // and that it does fit on one of the sides
  if (2 * MARGIN + width >= screenWidth ||
    (position.x + width + MARGIN >= screenWidth && position.x - width - MARGIN <= 0 )) {
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
  if (y < 0) y = position.y + MARGIN;
  if (y + height + MARGIN >= screenHeight) y = position.y - height - MARGIN;

  style.transform = `translate(${x}px,${y}px)`;

  return (
    <div id={id} className="tooltip panel" style={style} ref={ref}>
      {children}
    </div>
  );
};

export default connect(mapStateToProps)(TooltipContainer);
