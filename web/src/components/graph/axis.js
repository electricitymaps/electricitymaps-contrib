import React from 'react';

const Axis = ({
  className,
  label,
  scale,
  renderLine,
  renderTick,
  textAnchor,
  transform,
}) => (
  <g
    className={className}
    transform={transform}
    fill="none"
    fontSize="10"
    fontFamily="sans-serif"
    textAnchor={textAnchor}
    style={{ pointerEvents: 'none' }}
  >
    {label && <text className="label" transform="translate(35, 80) rotate(-90)">{label}</text>}
    <path className="domain" stroke="currentColor" d={renderLine(scale.range())} />
    {scale.ticks(5).map(renderTick)}
  </g>
);

export default Axis;
