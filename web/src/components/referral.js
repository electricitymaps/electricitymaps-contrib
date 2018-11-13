const d3 = Object.assign(
  {},
  require('d3-selection'),
);

export default class Referral {
  constructor(selectorId) {
    this.selectorId = selectorId;
    this.zone = [];
  }

  setReferralZone(zone) {
    this.zone = zone || [];
  }

  render() {
    if (this.zone === 'DK-DK2' || this.zone === 'DK-DK1') {
      const selector = d3.selectAll(this.selectorId);
      selector.selectAll('*').remove();
      selector.attr('class', 'referral-link')
        .attr('target', '_blank')
        .attr('href', '#');
      const refferalContent = selector.append('div')
        .attr('class', 'referral barry');
      refferalContent.append('p')
        .text('sponsored message')
        .attr('class', 'sponsored-message-text');
      refferalContent.append('p')
        .text('Know the footprint of your electricity consumption with barry')
        .attr('class', 'referral-text');
      refferalContent.append('img')
        .attr('src', 'images/barry.png')
        .attr('class', 'barry-logo');
      refferalContent.append('img')
        .attr('src', 'images/external-link.svg')
        .attr('class', 'external-link-icon');
    } else {
      const selector = d3.selectAll(this.selectorId);
      selector.selectAll('*').remove();
    }
  }
}
