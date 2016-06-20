function CountryMap(selector, co2color) {
    this.root = d3.select(selector);
    this.co2color = co2color;
    this.graticule = this.root
        .append('path')
        .attr('class', 'graticule');
    this.land = this.root.append('g');
}

CountryMap.prototype.render = function() {
    var computedMapWidth = this.root.node().getBoundingClientRect().width,
        computedMapHeight = this.root.node().getBoundingClientRect().height;

    this.projection = d3.geo.mercator()
        .center([3, 48])
        .translate([0.6 * computedMapWidth, 0.6 * computedMapHeight])
        .scale(700);

    this.path = d3.geo.path()
        .projection(this.projection);
        
    var graticuleData = d3.geo.graticule()
        .step([5, 5]);
        
    this.graticule
        .datum(graticuleData)
        .attr('d', this.path);
}

CountryMap.prototype.projection = function(arg) {
    if (!arg) return this.projection;
    else this.projection = arg;
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
        return this.data;
    } else {
        this.data = data;
        var that = this;
        this.land.selectAll('.country')
            .data(data)
            .enter()
                .append('path')
                .attr('class', 'country')
                .attr('d', this.path)
                .attr('stroke', 'black')
                .attr('stroke-width', 0.3)
                .attr('fill', function (d, i) { 
                    return (d.data.co2 !== undefined) ? that.co2color(d.data.co2) : 'gray';
                })
                .on('mouseover', function (d, i) {
                    return that.countryMouseOverHandler.call(this, d, i);
                })
                .on('mouseout', function (d, i) {
                    return that.countryMouseOutHandler.call(this, d, i);
                })
                .on('click', function (d, i) {
                    return that.countryClickHandler.call(this, d, i);
                });
    }
    return this;
};
