const d3 = Object.assign(
  {},
  require('d3-selection'),
  require('d3-scale'),
  require('d3-axis'),
);
const moment = require('moment');
const translation = require('../helpers/translation');


const TIME_FORMAT = 'LT'; // Localized time, e.g. "8:30 PM"
const NUMBER_OF_TICKS = 5;
const AXIS_MARGIN_LEFT = 5;

export default class TimeSlider {
  constructor(selector, dateAccessor) {
    this.rootElement = d3.select(selector);
    this.dateAccessor = dateAccessor;
    this._setup();
  }

  _setup() {
    this.slider = this.rootElement.append('input')
      .attr('type', 'range')
      .attr('class', 'time-slider-input');
    this.axisContainer = this.rootElement.append('svg')
      .attr('class', 'time-slider-axis-container');
    this.axis = this.axisContainer.append('g')
      .attr('class', 'time-slider-axis')
      .attr('transform', `translate(${AXIS_MARGIN_LEFT}, 0)`);

    const onChangeAndInput = () => {
      const selectedIndex = parseInt(this.slider.property('value'), 10);
      this._onChange(selectedIndex);
    };
    this.slider.on('input', onChangeAndInput);
    this.slider.on('change', onChangeAndInput);
  }

  render() {
    if (this._data && this._data.length) {
      const width = this.axisContainer.node().getBoundingClientRect().width - AXIS_MARGIN_LEFT;
      this.timeScale.range([0, width]);
      this._renderXAxis();
      this._updateSliderValue();
    }
    return this;
  }

  _renderXAxis() {
    const xAxis = d3.axisBottom(this.timeScale)
      .ticks(NUMBER_OF_TICKS)
      .tickSize(0)
      .tickValues(this.tickValues)
      .tickFormat((d, i) => {
        if (i === NUMBER_OF_TICKS - 1) {
          return translation.translate('country-panel.now');
        }
        return moment(d).format(TIME_FORMAT);
      });
    this.axis.call(xAxis);
    this.axis.selectAll('.tick text').attr('fill', '#000000');
  }

  _updateSliderValue() {
    if (this._selectedIndex) {
      this.slider.property('value', this._selectedIndex);
    } else {
      this.slider.property('value', this._data && this._data.length ? this._data.length : 0);
    }
  }

  data(data) {
    if (!arguments.length) return this._data;
    this._data = data.map(this.dateAccessor);
    this._setupSliderRange();
    this._setupSliderTimeScale();
    this._sampleTickValues();

    return this;
  }

  _setupSliderRange() {
    if (this._data && this.data.length) {
      this.slider.attr('min', 0);
      this.slider.attr('max', this._data.length - 1);
    }
  }

  _setupSliderTimeScale() {
    if (this._data && this.data.length) {
      this.timeScale = d3.scaleTime();
      const firstDate = moment(this._data[0]).toDate();
      const lastDate = moment(this._data[this._data.length - 1]).toDate();
      this.timeScale.domain([firstDate, lastDate]);
    }
  }

  _sampleTickValues() {
    this.tickValues = [];
    if (this._data.length >= NUMBER_OF_TICKS) {
      for (let i = 0; i < NUMBER_OF_TICKS; i++) {
        const sampleIndex = Math.floor(((this._data.length - 1) / (NUMBER_OF_TICKS - 1)) * (i));
        const sampledTimeStamp = this._data[sampleIndex];
        this.tickValues.push(moment(sampledTimeStamp).toDate());
      }
    }
  }

  selectedIndex(index, previousIndex) {
    this._selectedIndex = index || previousIndex;
    this.render();
    return this;
  }

  onChange(onChangeHandler) {
    this._onChange = onChangeHandler;
    return this;
  }
}
