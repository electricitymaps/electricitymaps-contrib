import React from 'react';
import { BaseControl } from 'react-map-gl';
import { connect } from 'react-redux';

const mapStateToProps = (state) => ({
  mapViewport: state.application.mapViewport,
});

// A proxy component that passes the projection methods to layers
// based on the current map state. Setting _containerRef in a wrapper
// is important for capturing mouse events (e.g. clicks) and not
// letting them propagate to the map.
class MapLayer extends BaseControl {
  state = {
    project: null,
    unproject: null,
  };

  // Keep project and unproject methods in the component state and update them
  // only when the map viewport changes as ReactMapGL calls the _render() method
  // at all sorts of times and we don't want the layers to rerender more than needed.
  // Always set in the next cycle to make sure it's not picking up old methods.
  componentWillReceiveProps(nextProps) {
    if (nextProps.mapViewport !== this.props.mapViewport) {
      setTimeout(() => {
        this.setState({
          project: this._context.viewport.project,
          unproject: this._context.viewport.unproject,
        });
      }, 0);
    }
  }

  _render() {
    return (
      <div ref={this._containerRef}>
        <this.props.component
          project={this.state.project || this._context.viewport.project}
          unproject={this.state.unproject || this._context.viewport.unproject}
        />
      </div>
    );
  }
}

// Pass through all drag events to the map.
MapLayer.defaultProps.captureDrag = false;

export default connect(mapStateToProps)(MapLayer);
