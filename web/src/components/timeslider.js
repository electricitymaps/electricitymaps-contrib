const d3 = Object.assign(
  {},
  require('d3-selection'),
  require('d3-scale'),
  require('d3-axis'),
);
const moment = require('moment');

const NUMBER_OF_TICKS = 5;

export default class TimeSlider {
  constructor(selector, dateAccessor) {
    this.rootElement = d3.select(selector);
    this.dateAccessor = dateAccessor;
    this._setup();
  }

  _setup() {
    this.slider = this.rootElement.append('input').attr('type', 'range');
    this.axisContainer = this.rootElement.append('svg').attr('class', 'time-slider-axis-container');
    this.axis = this.axisContainer.append('g').attr('class', 'time-slider-axis');
    this.slider.on('input', () => {
      const selectedIndex = this.slider.property('value');
      this._manuallySelectedIndex = selectedIndex;
      this._onChange(selectedIndex);
    });
  }

  render() {
    if (this._data && this._data.length) {
      this.timeScale.range([0, this.slider.node().getBoundingClientRect().width]);
      const xAxis = d3.axisBottom(this.timeScale)
        .ticks(NUMBER_OF_TICKS)
        .tickSize(0)
        .tickValues(this.tickValues)
        .tickFormat((d, i) => {
          if (i === NUMBER_OF_TICKS - 1) {
            return 'Now'; // TODO: Translate
          }
          return moment(d).format('LT');
        });
      this.axis.call(xAxis);
      if (this._selectedIndex) {
        this.slider.property('value', this._selectedIndex);
      } else {
        this.slider.property('value', this._data && this._data.length ? this._data.length : 0);
      }
    }

    return this;
  }

  data(data) {
    if (!arguments.length) return this._data;
    this._data = data.map(this.dateAccessor);
    this.slider.attr('min', 0);
    this.slider.attr('max', this._data.length - 1);
    this.timeScale = d3.scaleTime();
    this.timeScale.domain([moment(this._data[0]).toDate(), moment(this._data[this._data.length - 1]).toDate()]);
    this.tickValues = [];
    if (this._data.length >= NUMBER_OF_TICKS) {
      for (let i = 0; i < NUMBER_OF_TICKS; i++) {
        // TODO: Refactor/simplify
        this.tickValues.push(moment(this._data[Math.floor(((this._data.length - 1) / (NUMBER_OF_TICKS - 1)) * (i))]).toDate());
      }
    }

    return this;
  }

  selectedIndex(index) {
    this._selectedIndex = index || this._manuallySelectedIndex;
    this.render();
    return this;
  }

  onChange(onChangeHandler) {
    this._onChange = onChangeHandler;
    return this;
  }
}
