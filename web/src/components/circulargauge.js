const d3 = Object.assign(
  {},
  require('d3-selection'),
  require('d3-transition'),
  require('d3-shape'),
  require('d3-interpolate'),
);

export default class CircularGauge {
  constructor(selectorId, argConfig) {
    const config = argConfig || {};

    this.radius = config.radius || '32';
    this.lineWidth = config.lineWidth || '6';
    this.fontSize = config.fontSize || '1rem';

    this.arc = d3.arc()
      .startAngle(0)
      .innerRadius(this.radius - this.lineWidth)
      .outerRadius(this.radius);

    this.prevPercentage = 0;

    this.percentage = config.percentage || null;

    // main gauge component

    const gauge = d3.select(`#${selectorId}`).append('svg')
      .attr('width', this.radius * 2)
      .attr('height', this.radius * 2)
      // .attr("width", '100%') // makes gauge auto-resize
      // .attr("height", '100%') // makes gauge auto-resize
    // .attr("viewBox", "0 0 " + (this.radius * 2) + " " + (this.radius * 2)) // makes resizable
    // .attr("preserveAspectRatio", "xMidYMid meet") // makes gauge resizable
      .append('g')
      .attr('transform', `translate(${this.radius},${this.radius})`)
      .append('g')
      .attr('class', 'circular-gauge');

    // background
    this.background = gauge.append('path')
      .attr('class', 'background')
      .attr('d', this.arc.endAngle(2 * Math.PI));

    // foreground
    this.foreground = gauge.append('path')
      .attr('class', 'foreground')
      .attr('d', this.arc.endAngle(0)); // starts filling from 0

    this.percentageText = gauge.append('text')
      .style('text-anchor', 'middle')
      .attr('dy', '0.4em')
      .style('font-weight', 'bold')
      .style('font-size', this.fontSize)
      .text(this.percentage != null ? `${Math.round(this.percentage)}%` : '?');

    this.draw();
  }

  draw() {
    const arc = this.arc;
    const prevPercentage = this.prevPercentage != null ? this.prevPercentage / 100 : 0;
    const percentage = this.percentage != null ? this.percentage / 100 : 0;

    const i = d3.interpolate(prevPercentage * 2 * Math.PI, 2 * Math.PI * (percentage));

    this.foreground.transition()
      .duration(500)
      .attrTween(
        'd',
        () => t => arc.endAngle(i(t))(),
      );
  }

  setPercentage(percentage) {
    if (this.percentage === percentage) {
      return;
    }
    if (Number.isNaN(percentage)) {
      return;
    }
    this.prevPercentage = this.percentage;
    this.percentage = percentage;
    this.percentageText.text(this.percentage != null ? `${Math.round(this.percentage)}%` : '?');
    this.draw();
  }
}
