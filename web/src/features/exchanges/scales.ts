import { scaleLinear, scaleQuantize } from 'd3-scale';
import { colors } from 'hooks/colors';
import { MapColorSource } from 'utils/constants';

// The following are the values in which the arrowfiles are generated
const arrowfileColors = [0, 80, 160, 240, 320, 400, 480, 560, 640, 720, 800];
const maxCo2Scale = Math.max(
  ...colors.bright.colorScale[MapColorSource.CARBON_INTENSITY].domain()
); // note: this assumes the scale max is the same for bright and dark themes
const maxArrowFileColor = Math.max(...arrowfileColors);

export const colorValueDomain: { [key in MapColorSource]: number[] } = {
  // Domains are from cleanest to dirtiest
  [MapColorSource.CARBON_INTENSITY]: [0, maxArrowFileColor], // map scale goes to 1500, but ok as we just ignore above
  [MapColorSource.RENEWABLE_PERCENTAGE]: [100, 100 * (maxArrowFileColor / maxCo2Scale)], // scale shouldn't go to 0% as we haven't generated arrows for very dirty values (high CI, low RE)
};

export function generateQuantizedColorScale(mapColorSource: MapColorSource) {
  let domain = colorValueDomain[mapColorSource];
  let range = arrowfileColors;
  // scaleQuantize only supports ascending domains
  if (domain[0] > domain[1]) {
    range = range.toReversed();
    domain = domain.toReversed();
  }
  return scaleQuantize().domain(domain).range(range).unknown('nan');
}

export const quantizedExchangeSpeedScale = scaleLinear()
  .domain([500, 5000])
  .rangeRound([0, 2])
  .unknown(0)
  .clamp(true);
