var d3 = require('d3');

function CountryMap(selector, co2color) {
    var that = this;

    this.STROKE_WIDTH = 0.3;
    this.STROKE_COLOR = '#555555';

    this.selectedCountry = undefined;

    this.root = d3.select(selector)
        .data([ {'x':0, 'y':0} ]); // For dragging
    this.co2color = co2color;
    this.graticule = this.root
        .on('touchstart click', function (d, i) {
            if (that.selectedCountry !== undefined) {
                that.selectedCountry
                    .style('stroke', that.STROKE_COLOR)
                    .style('stroke-width', that.STROKE_WIDTH);
            }
            if (that.seaClickHandler)
                that.seaClickHandler.call(this, d, i);
        })
        .append('path')
            .attr('class', 'graticule');
    this.land = this.root.append('g');
    
    // Prepare drag
    this.drag = d3.drag()
        .on('start', function() {
            //console.log('start', d3.event);
            d3.select(this).style('cursor', 'move');
        })
        .on('drag', function(d, i) {
            //console.log(d);
            d.x += d3.event.dx;
            d.y += d3.event.dy;
            d3.select(this).style('transform', function(d, i) {
                return 'translate(' + d.x + 'px' + ',' + d.y + 'px' + ')';
            });
        })
        .on('end', function() {
            //console.log('end', d3.event);
            d3.select(this).style('cursor', undefined);
        });

    this.root.call(this.drag);
}

CountryMap.prototype.render = function() {
    var clientWidth = document.body.clientWidth;
    var clientHeight = document.body.clientHeight;

    // Center of the map
    var center = [0, 54];
    // Determine scale (i.e. zoom) based on the shortest dimension
    var scale = Math.max(1100, 0.8 * Math.min(clientWidth, clientHeight));
    // Determine map width and height based on bounding box of Europe
    var sw = [-10, 34.7];
    var ne = [34, 72];
    this._projection = d3.geoTransverseMercator()
        .rotate([-center[0], -center[1]])
        .scale(scale);
    var projected_sw = this._projection(sw);
    var projected_ne = this._projection(ne);
    // This is a curved representation, so take all 4 corners in order to make
    // sure we include them all
    var se = [ne[0], sw[1]];
    var nw = [sw[0], ne[1]];
    var projected_se = this._projection(se);
    var projected_nw = this._projection(nw);
    var mapWidth = Math.max(projected_ne[0], projected_se[0]) -
        Math.min(projected_sw[0], projected_nw[0]); // TODO: Never do width < 100% !
    var mapHeight = Math.max(projected_sw[1], projected_se[1]) -
        Math.min(projected_ne[1], projected_nw[1]);
    // Width and height should nevertheless never be smaller than the container
    mapWidth  = Math.max(mapWidth,  this.root.node().parentNode.getBoundingClientRect().width);
    mapHeight = Math.max(mapHeight, this.root.node().parentNode.getBoundingClientRect().height);

    this.root
        .style('height', mapHeight)
        .style('width', mapWidth);
    this._projection
        .translate([0.5 * projected_sw[0], 0.5 * projected_sw[1]]);

    this.path = d3.geoPath()
        .projection(this._projection);
        
    var graticuleData = d3.geoGraticule()
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
                    if (that.countryMouseOverHandler)
                        return that.countryMouseOverHandler.call(this, d, i);
                })
                .on('mouseout', function (d, i) {
                    if (that.countryMouseOutHandler)
                        return that.countryMouseOutHandler.call(this, d, i);
                })
                .on('mousemove', function (d, i) {
                    if (that.countryMouseMoveHandler)
                        return that.countryMouseMoveHandler.call(this, d, i);
                })
                .on('touchstart click', function (d, i) {
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
                })
            .merge(selector)
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

CountryMap.prototype.onCountryMouseMove = function(arg) {
    if (!arg) return this.countryMouseMoveHandler;
    else this.countryMouseMoveHandler = arg;
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

module.exports = CountryMap;
