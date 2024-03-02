import { showEstimationFeedbackCard } from './util';

describe('showEstimationFeedbackCard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should return true when feedbackCard is currently not shown, card has not been seen before and it has been collapsed', () => {
    const result = showEstimationFeedbackCard(1, false, false, () => {});
    expect(result).to.equal(true);
  });

  it('should return true when isFeedbackCardVisibile is true', () => {
    const result = showEstimationFeedbackCard(1, true, true, () => {});
    expect(result).to.equal(true);
  });

  it('should return false when conditions are not met', () => {
    const result = showEstimationFeedbackCard(0, false, true, () => {});
    expect(result).to.equal(false);
  });

  it('should return false when conditions are not met', () => {
    const result = showEstimationFeedbackCard(2, false, true, () => {});
    expect(result).to.equal(false);
  });
});
