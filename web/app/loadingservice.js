var exports = module.exports = {};

var d3 = require('d3');

var stack = {};

exports.startLoading = function(selector) {
    selector = selector || '#loading';
    stack[selector] = stack[selector] || [];
    if (!stack[selector].length) {
        d3.selectAll(selector)
            .style('display', 'block')
            .transition()
            .style('opacity', 0.8);
    }
    stack[selector].push(undefined);
}

exports.stopLoading = function(selector) {
    selector = selector || '#loading';
    stack[selector].pop();
    if (!stack[selector].length) {
        d3.selectAll(selector)
            .transition()
                .style('opacity', 0)
                .on('end', function() {
                    d3.select(this).style('display', 'none');
                });
    }
}
