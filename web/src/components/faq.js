const translation = require('../helpers/translation');

const d3 = Object.assign(
  {},
  require('d3-selection'),
);

const QnATexts = [
  { question: 'What is this map?', answer: 'This map is the worlds best map and thank you for being here' },
  { question: 'Why are high-nuclear countries green?', answer: 'Because nuclear is very good for the world and why are you even asking?' },
];


export default class FAQ {
  constructor(selectorId, argConfig) {
    this.selector = d3.select(selectorId);
    this._setup();
  }

  _setup() {
    this.container = this.selector.append('div').attr('class', 'faq-container');
    this.QnAs = [];
    QnATexts.forEach((item, index) => {
      this._createQuestionAndAnswer(item.question, item.answer, index);
    });
  }
  _createQuestionAndAnswer(questionText, answerText, index) {
    const QnAContainer = this.container.append('div').attr('class', 'question-answer-container');
    const question = QnAContainer.append('div').attr('class', 'question').text(questionText);
    const answer = QnAContainer.append('div').attr('class', 'answer').text(answerText);
    question.on('click', () => this._toggleAnswer(index));
    this.QnAs[index] = { question, answer };
  }

  _toggleAnswer(index) {
    this.QnAs[index].answer.classed('visible', !this.QnAs[index].isExpanded);
    this.QnAs[index].isExpanded = !this.QnAs[index].isExpanded;
  }
}
