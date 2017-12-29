const exports = module.exports = {};

const d3 = require('d3-selection');

const stack = {};

exports.startLoading = (selector) => {
  stack[selector] = stack[selector] || [];
  if (!stack[selector].length) {
    d3.selectAll(selector)
      .style('display', 'block')
      .transition()
      .style('opacity', 0.8);
  }
  stack[selector].push(undefined);
};

exports.stopLoading = (selector) => {
  stack[selector].pop();
  if (!stack[selector].length) {
    console.log(selector)
    d3.selectAll(selector)
      .transition()
        .style('opacity', 0)
        .on('end', function() {
            d3.select(this).style('display', 'none');
        });
  }
};
