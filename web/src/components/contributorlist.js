const d3 = Object.assign(
  {},
  require('d3-selection'),
);

export default class ContributorList {
  constructor(selectorId) {
    this.selectorId = selectorId;
    this.contributors = [];
  }

  setContributors(contributors) {
    this.contributors = contributors || [];
  }

  render() {
    const selector = d3.selectAll(this.selectorId).selectAll('a').data(this.contributors);
    const enterA = selector.enter().append('a')
      .attr('target', '_blank');
    const enterImg = enterA.append('img');
    enterA.merge(selector)
      .attr('href', d => d);
    enterImg.merge(selector.select('img'))
      .attr('src', d => `${d}.png`);
    selector.exit().remove();
  }
}
