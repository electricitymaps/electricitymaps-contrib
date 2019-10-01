const d3 = Object.assign(
  {},
  require('d3-selection'),
);
const { getState } = require('../store');
const thirdPartyServices = require('../services/thirdparty');

const matchingZones = ['DK-DK1', 'DK-DK2', 'DK-BHM'];

export default class Referral {
  constructor(selectorId) {
    this.selectorId = selectorId;
  }

  setSelectedZone(selectedZone) {
    this.selectedZone = selectedZone;
  }

  setCallerZone(callerZone) {
    this.callerZone = callerZone;
  }

  isVisible() {
    if (matchingZones.indexOf(this.selectedZone) !== -1 && matchingZones.indexOf(this.callerZone) !== -1) {
      return true;
    }
    return false;
  }

  render() {
    if (this.isVisible()) {
      const selector = d3.selectAll(this.selectorId);
      selector.selectAll('*').remove();
      selector.attr('class', 'referral-link');
      selector.append('p')
        .text('sponsored message')
        .attr('class', 'sponsored-message-text')
        .append('a')
        .text(' - hide')
        .attr('class', 'hide-referral')
        .on('click', () => {
          selector.selectAll('*').remove();
        });
      const refferalContent = selector.append('a')
        .attr('class', 'referral barry')
        .attr('target', '_blank')
        .attr('href', 'https://getbarry.app.link/Snhrg3wqmZ')
        .on('click', () => {
          thirdPartyServices.trackWithCurrentApplicationState('referralClicked');
        });
      refferalContent.append('p')
        .text('Se hvordan Barry, app\'en til din strøm, bruger vores data')
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
