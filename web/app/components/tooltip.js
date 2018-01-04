var d3 = require('d3');

function placeTooltip(selector, eventX, eventY) {
    var tooltip = d3.select(selector);
    var w = tooltip.node().getBoundingClientRect().width;
    var h = tooltip.node().getBoundingClientRect().height;
    var margin = 7;
    var screenWidth = window.innerWidth;

    var x = 0;
    var y = 0;
    // Check that tooltip is not larger than screen
    // and that it does fit on one of the sides
    if (2 * margin + w >= screenWidth ||
        (eventX + w + margin >= screenWidth && eventX - w - margin <= 0 ))
    {
        tooltip.style('width', '100%');
    }
    else {
        x = eventX + margin;
        // Check that tooltip does not go over the right bound
        if (w + x >= screenWidth) {
            // Put it on the left side
            x = eventX - w - margin;
        }
    }
    y = eventY - h - margin;
    if (y < 0) y = eventY + margin;
    tooltip
        .style('transform',
            'translate(' + x + 'px' + ',' + y + 'px' + ')');
}

function Tooltip(selector) {
    this._selector = selector
    var that = this;
    d3.select(this._selector)
        .style('opacity', 0)
        // For mobile, hide when tapped
        .on('click', function(e) { that.hide(); d3.event.stopPropagation(); })
    return this;
}

Tooltip.prototype.show = function() {
    if (this.isShowing) { return; }
    this.isShowing = true;
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
    d3.select(this._selector)
        .transition()
        .style('opacity', 0)
        .on('end', function() {
            d3.select(this).style('display', 'none');
        });
    return this;
}

module.exports = Tooltip
