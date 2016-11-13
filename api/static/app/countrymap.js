function CountryMap(selector, co2color) {
    var that = this;

    this.STROKE_WIDTH = 0.3;
    this.STROKE_COLOR = '#555555';

    this.selectedCountry = undefined;

    this.root = d3.select(selector);
    this.co2color = co2color;
    this.graticule = this.root
        .on('click', function (d, i) {
            if (that.selectedCountry !== undefined) {
                that.selectedCountry
                    .style('stroke', that.STROKE_COLOR)
                    .style('stroke-width', that.STROKE_WIDTH);
            }
            that.seaClickHandler.call(this, d, i);
        })
        .append('path')
            .attr('class', 'graticule');
    this.land = this.root.append('g');
}

CountryMap.prototype.render = function() {
    var computedMapWidth = this.root.node().getBoundingClientRect().width,
        computedMapHeight = this.root.node().getBoundingClientRect().height;

    this._projection = d3.geo.mercator()
        .center([3, 48])
        .translate([0.55 * computedMapWidth, 0.65 * computedMapHeight])
        .scale(650);

    this.path = d3.geo.path()
        .projection(this._projection);
        
    var graticuleData = d3.geo.graticule()
        .step([5, 5]);
        
    this.graticule
        .datum(graticuleData)
        .attr('d', this.path);

    var that = this;
    if (this._data) {
        var getCo2Color = function (d) {
            return (d.co2intensity !== undefined) ? that.co2color(d.co2intensity) : 'gray';
        };
        var selector = this.land.selectAll('.country')
            .data(this._data, function(d) { return d.countryCode; });
        selector.enter()
                .append('path')
                .attr('class', 'country')
                .attr('stroke', that.STROKE_COLOR)
                .attr('stroke-width', that.STROKE_WIDTH)
                .attr('fill', getCo2Color)
                .on('mouseover', function (d, i) {
                    return that.countryMouseOverHandler.call(this, d, i);
                })
                .on('mouseout', function (d, i) {
                    return that.countryMouseOutHandler.call(this, d, i);
                })
                .on('click', function (d, i) {
                    d3.event.stopPropagation(); // To avoid call click on sea
                    if (that.selectedCountry !== undefined) {
                        that.selectedCountry
                            .style('stroke', that.STROKE_COLOR)
                            .style('stroke-width', that.STROKE_WIDTH);
                    }
                    that.selectedCountry = d3.select(this);
                    // that.selectedCountry
                    //     .style('stroke', 'darkred')
                    //     .style('stroke-width', 1.5);
                    return that.countryClickHandler.call(this, d, i);
                });
        selector
            .attr('d', this.path)
            .transition()
            .duration(2000)
            .attr('fill', getCo2Color);
    }
}

CountryMap.prototype.projection = function(arg) {
    if (!arg) return this._projection;
    else this._projection = arg;
    return this;
};

CountryMap.prototype.onSeaClick = function(arg) {
    if (!arg) return this.seaClickHandler;
    else this.seaClickHandler = arg;
    return this;
};

CountryMap.prototype.onCountryClick = function(arg) {
    if (!arg) return this.countryClickHandler;
    else this.countryClickHandler = arg;
    return this;
};

CountryMap.prototype.onCountryMouseOver = function(arg) {
    if (!arg) return this.countryMouseOverHandler;
    else this.countryMouseOverHandler = arg;
    return this;
};

CountryMap.prototype.onCountryMouseOut = function(arg) {
    if (!arg) return this.countryMouseOutHandler;
    else this.countryMouseOutHandler = arg;
    return this;
};

CountryMap.prototype.data = function(data) {
    if (!data) {
        return this._data;
    } else {
        this._data = data;
    }
    return this;
};
