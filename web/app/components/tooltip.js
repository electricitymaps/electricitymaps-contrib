var d3 = require('d3');

function placeTooltip(selector, d3Event) {
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
            x = d3Event.clientX + margin;
            if (screenWidth - x <= w) {
                x = d3Event.clientX - w - margin;
            }
        }
        var y = d3Event.clientY - h - margin; if (y <= margin) y = d3Event.clientY + margin;
        tooltip
            .style('transform',
                'translate(' + x + 'px' + ',' + y + 'px' + ')');
    }
}

function Tooltip(selector) {
    this._selector = selector
    return this;
}

Tooltip.prototype.show = function(d3Event) {
    d3.select(this._selector)
        .style('display', 'inline');
    return this;
}
Tooltip.prototype.update = function(d3Event) {
    placeTooltip(this._selector, d3Event);
    return this;
}
Tooltip.prototype.hide = function() {
    d3.select(this._selector)
        .style('display', 'none');
    return this;
}

module.exports = Tooltip
