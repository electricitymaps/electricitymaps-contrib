var d3 = require('d3');

function placeTooltip(selector, eventX, eventY) {
    var tooltip = d3.select(selector);
    var w = tooltip.node().getBoundingClientRect().width;
    var h = tooltip.node().getBoundingClientRect().height;
    var margin = 7;
    var screenWidth = window.innerWidth;
    // On very small screens
    if (w > screenWidth) {
        tooltip
            .style('width', '100%');
    }
    else {
        var x = 0;
        if (w > screenWidth / 2 - 5) {
            // Tooltip won't fit on any side, so don't translate x
            x = 0.5 * (screenWidth - w);
        } else {
            x = eventX + margin;
            if (screenWidth - x <= w) {
                x = eventX - w - margin;
            }
        }
        var y = eventY - h - margin;
        if (y <= margin) y = eventY + margin;
        tooltip
            .style('transform',
                'translate(' + x + 'px' + ',' + y + 'px' + ')');
    }
}

function Tooltip(selector) {
    this._selector = selector
    var that = this;
    d3.select(this._selector)
        // For mobile, hide when tapped
        .on('click', function(e) { that.hide(); d3.event.stopPropagation(); })
    return this;
}

Tooltip.prototype.show = function() {
    d3.select(this._selector)
        .classed('visible', true);
    return this;
}
Tooltip.prototype.update = function(x, y) {
    placeTooltip(this._selector, x, y);
    return this;
}
Tooltip.prototype.hide = function() {
    d3.select(this._selector)
        .classed('visible', false);
    return this;
}

module.exports = Tooltip
