import { event as d3Event } from 'd3-selection';

const d3 = Object.assign(
  {},
  require('d3-selection'),
  require('d3-transition'),
);

function placeTooltip(selector, eventX, eventY) {
  const tooltip = d3.select(selector);
  const w = tooltip.node().getBoundingClientRect().width;
  const h = tooltip.node().getBoundingClientRect().height;
  const margin = 16;
  const screenWidth = window.innerWidth;
  const screenHeight = window.innerHeight;

  let x = 0;
  let y = 0;
  // Check that tooltip is not larger than screen
  // and that it does fit on one of the sides
  if (2 * margin + w >= screenWidth ||
    (eventX + w + margin >= screenWidth && eventX - w - margin <= 0 )) {
    // TODO(olc): Once the tooltip has taken 100% width, it's width will always be 100%
    // as we base our decision to revert based on the current width
    tooltip.style('width', '100%');
  } else {
    x = eventX + margin;
    // Check that tooltip does not go over the right bound
    if (w + x >= screenWidth) {
      // Put it on the left side
      x = eventX - w - margin;
    }
  }
  y = eventY - margin - h;
  if (y < 0) y = eventY + margin;
  if (y + h + margin >= screenHeight) y = eventY - h - margin;
  // y = eventY
  tooltip
    .style('transform', `translate(${x}px,${y}px)`);
}

function Tooltip(selector) {
    this._selector = selector
    var that = this;
    d3.select(this._selector)
        .style('opacity', 0)
        // For mobile, hide when tapped
        .on('click', function(e) { that.hide(); d3Event.stopPropagation(); })
    return this;
}

Tooltip.prototype.show = function() {
    if (this.isShowing) { return; }
    this.isShowing = true;
    this.isVisible = true;
    d3.select(this._selector)
        .style('display', 'block')
        .transition()
        .style('opacity', 1)
        .on('end', () => { this.isShowing = false; });
    return this;
}
Tooltip.prototype.update = function(x, y) {
    placeTooltip(this._selector, x, y);
    return this;
}
Tooltip.prototype.hide = function() {
    this.isShowing = false;
    this.isVisible = false;
    d3.select(this._selector)
        .style('width', null) // this is a temporary fix for the 100% width problem
        .transition()
        .style('opacity', 0)
        .on('end', function() {
            d3.select(this).style('display', 'none');
        });
    return this;
}

module.exports = Tooltip
