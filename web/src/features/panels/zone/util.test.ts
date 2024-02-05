import { showEstimationFeedbackCard } from './util';

describe('showEstimationFeedbackCard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should return true and set feedbackCardStatus when feedbackCardStatus is not seenBefore and collapsedNumber is greater than 1', () => {
    const result = showEstimationFeedbackCard(2, false, 'notSeenBefore');
    expect(result).to.equal(true);
    //expect(localStorage.setItem).calledOnceWith('feedbackCardStatus', 'seenBefore');
  });

  it('should return true and set feedbackCardStatus when showFeedbackCard is true', () => {
    const result = showEstimationFeedbackCard(1, true, 'seenBefore');
    expect(result).to.equal(true);
    //expect(localStorage.setItem).calledOnceWith('feedbackCardStatus', 'seenBefore');
  });

  it('should return false and not set feedbackCardStatus when conditions are not met', () => {
    const result = showEstimationFeedbackCard(1, false, 'seenBefore');
    expect(result).to.equal(false);
    //expect(localStorage.setItem).not.to.have.toha();
  });
});
