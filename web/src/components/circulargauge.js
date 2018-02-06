'use strict';

const d3 = Object.assign(
  {},
  require('d3-selection'),
  require('d3-transition'),
  require('d3-shape')
);

class CircularGauge {

  constructor(selectorId, argConfig) {
    const config = argConfig || {};

    this.radius = config.radius || "100";
    this.lineWidth = config.lineWidth || "20";
    this.fontSize = config.fontSize || "60px";

    this.arc = d3.arc()
      .startAngle(0)
      .innerRadius(this.radius - this.lineWidth)
      .outerRadius(this.radius);

    this.prevPercentage = 0;
    this.percentage = config.percentage || "0";

    var gauge = d3.select(`#${selectorId}`).append("svg")
      .attr("width", this.radius * 2)
      .attr("height", this.radius * 2)
      .append("g")
      .attr("transform", "translate(" + this.radius + "," + this.radius + ")")
      .append("g")
      .attr("class", "circular-gauge");

    // background
    gauge.append("path")
      .attr("class", "background")
      .attr("d", this.arc.endAngle(2 * Math.PI));

    // foreground
    this.foreground = gauge.append("path")
      .attr("class", "foreground")
      .attr("d", this.arc.endAngle(0)); // starts filling from 0

    this.percentageText = gauge.append("text")
      .attr("font-size", this.fontSize)
      .attr("text-anchor", "middle")
      .attr("alignment-baseline", "central")
      .text(`${this.percentage}%`)

    this.draw();

  }

  draw() {

    var arc = this.arc
    var prevPercentage = this.prevPercentage / 100
    var percentage = this.percentage / 100

    var i = d3.interpolate(prevPercentage * 2 * Math.PI, (percentage) * 2 * Math.PI);

    this.foreground.transition()
      .duration(500)
      .attrTween("d",
        () => t => arc.endAngle(i(t))()
      );
  }

  setPercentage(percentage) {

    this.prevPercentage = this.percentage;
    this.percentage = percentage;
    this.percentageText.text(`${percentage}%`)
    this.draw();

  }
}
