import { showEstimationFeedbackCard } from './util';

describe('showEstimationFeedbackCard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should return true when feedbackCard is currently not shown, card has not been seen before and it has been collapsed more than once', () => {
    const result = showEstimationFeedbackCard(2, false, 'notSeenBefore');
    expect(result).to.equal(true);
  });

  it('should return true when showFeedbackCard is true', () => {
    const result = showEstimationFeedbackCard(1, true, 'seenBefore');
    expect(result).to.equal(true);
  });

  it('should return false when conditions are not met', () => {
    const result = showEstimationFeedbackCard(1, false, 'seenBefore');
    expect(result).to.equal(false);
  });

  it('should return false when conditions are not met', () => {
    const result = showEstimationFeedbackCard(2, false, 'seenBefore');
    expect(result).to.equal(false);
  });
});
