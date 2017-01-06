var exports = module.exports = {};

var d3 = require('d3');

var stack = [];

exports.startLoading = function() {
    if (!stack.length) {
        d3.select('.loading')
            .style('display', 'block')
            .transition()
            .style('opacity', 0.8);
    }
    stack.push(undefined);
}

exports.stopLoading = function() {
    stack.pop();
    if (!stack.length) {
        d3.select('.loading')
            .transition()
                .style('opacity', 0)
                .on('end', function() {
                    d3.select(this).style('display', 'none');
                });
    }
}
