'use babel';

import React from 'react'
import ReactDOM from 'react-dom';

import SourceMarker from '../marker';
import INNPVStore from '../stores/innpv_store';
import PerfHintState from '../models/PerfHintState';

function Increase() {
  return (
    <div className="innpv-perfhint">
      <span className="icon icon-arrow-up" />Increase
    </div>
  );
}

function Decrease() {
  return (
    <div className="innpv-perfhint">
      <span className="icon icon-arrow-down" />Decrease
    </div>
  );
}

class PerfHint extends React.Component {
  constructor(props) {
    super(props);
    this._marker = new SourceMarker(INNPVStore.getEditor());
    this._el = document.createElement('div');
  }

  componentDidMount() {
    this._marker.register(this.props.perfHint.getLocation());
  }

  componentDidUpdate(prevProps) {
    this._marker.reconcileLocation(
      prevProps.perfHint.getLocation(),
      this.props.perfHint.getLocation(),
    );
    if (prevProps.perfHintState === PerfHintState.NONE &&
        this.props.perfHintState !== PerfHintState.NONE) {
      this._showDecoration();
    } else if (prevProps.perfHintState !== PerfHintState.NONE &&
        this.props.perfHintState === PerfHintState.NONE) {
      this._hideDecoration();
    }
  }

  componentWillUnmount() {
    this._marker.remove();
  }

  _showDecoration() {
    this._marker.showDecoration({type: 'overlay', item: this._el});
  }

  _hideDecoration() {
    this._marker.hideDecoration();
  }

  _renderDecoration() {
    let showIncreasing = this.props.perfHintState === PerfHintState.INCREASING;
    if (!this.props.perfHint.getNaturalDirection()) {
      showIncreasing = !showIncreasing;
    }
    return showIncreasing ? <Increase /> : <Decrease />;
  }

  render() {
    if (this.props.perfHintState === PerfHintState.NONE) {
      return null;
    }
    return ReactDOM.createPortal(this._renderDecoration(), this._el);
  }
}

PerfHint.defaultProps = {
  perfHintState: PerfHintState.NONE,
};

export default PerfHint;
