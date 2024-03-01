import { animated, useSpring } from '@react-spring/web';
import useGetZone from 'api/getZone';
import { getTotalEmissionsAvailable } from 'features/charts/graphUtils';
import { AreaGraphElement } from 'features/charts/types';
import { useAtom } from 'jotai';
import {
  productionConsumptionAtom,
  reduceEmissionsAtom,
  selectedDatetimeIndexAtom,
  selectedFutureDatetimeIndexAtom,
  timeAverageAtom,
} from 'utils/state/atoms';
import { CarbonUnits } from 'utils/units';

import { useCo2ColorScale } from '../hooks/theme';

/**
 * This function finds the optimal text color based on a custom formula
 * derived from the W3CAG standard (see https://www.w3.org/TR/WCAG20-TECHS/G17.html).
 * I changed the original formula from Math.sqrt(1.05 * 0.05) - 0.05 to
 * Math.sqrt(1.05 * 0.18) - 0.05. Because this expression is a constant
 * I replaced it with it's approached value (0.3847...) to avoid useless computations.
 * See https://github.com/electricitymaps/electricitymaps-contrib/issues/3365 for more informations.
 * @param {string} rgbColor a string with the background color (e.g. "rgb(0,5,4)")
 */
const getTextColor = (rgbColor: string) => {
  const colors = rgbColor.replaceAll(/[^\d,.]/g, '').split(',');
  const r = Number.parseInt(colors[0], 10);
  const g = Number.parseInt(colors[1], 10);
  const b = Number.parseInt(colors[2], 10);
  const rgb = [r, g, b].map((c) => {
    const s = c / 255;
    return s <= 0.039_28 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  const luminosity = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
  return luminosity >= 0.384_741_302_385_683_16 ? 'black' : 'white';
};

function calculateTemporaryChange(
  emissions: number,
  decadeFromStart: number,
  reduceEmissions: boolean
) {
  // Calculates the total temperature change with diminishing returns for each decade.

  // Args:
  //     emissions: The emission rate in grams per unit (hour, day, month, or year).
  //     timeUnit: The unit of time for the emission rate ("hour", "day", "month", or "year").
  //     decadeFromStart: The number of decades for which to calculate the temperature change.
  //     reduceEmissions: Optional boolean flag (default: false) to enable reduction in emissions over time.

  // Returns:
  //     The total temperature change in degrees Celsius.

  // Convert emissions to grams per year

  const emissionsPerYear = emissions * 24 * 365;

  // Calculate total emissions with diminishing returns
  let totalEmissions = 0;
  let multiplier = 1;
  for (let index = 0; index < decadeFromStart; index++) {
    totalEmissions += emissionsPerYear * multiplier;
    if (reduceEmissions) {
      multiplier *= 0.5;
    } // Reduce emissions per decade
    if (!reduceEmissions) {
      multiplier = 1;
    } // Reduce emissions per decade
  }

  const totalEmissionsPg = totalEmissions / 1e15;
  const TCRE = 1.6; // Transient Climate Response to Cumulative Emissions (°C / PgC) (low end of the range)
  // Calculate temperature change using the provided conversion factor
  const temporaryChange = (totalEmissionsPg * TCRE) / 1000;

  return temporaryChange;
}

interface CarbonIntensitySquareProps {
  intensity: number;
  withSubtext?: boolean;
}

function CarbonIntensitySquare({ intensity, withSubtext }: CarbonIntensitySquareProps) {
  const co2ColorScale = useCo2ColorScale();
  const [mixMode] = useAtom(productionConsumptionAtom);
  const [reduceEmissions] = useAtom(reduceEmissionsAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [selectedFutureDatetime] = useAtom(selectedFutureDatetimeIndexAtom);
  const { data, isLoading } = useGetZone();
  const backgroundColor = useSpring({
    backgroundColor: co2ColorScale(intensity),
  }).backgroundColor;

  if (!data || isLoading) {
    return null;
  }

  const chartData: AreaGraphElement[] = Object.entries(data.zoneStates).map(
    ([datetimeString, value]) => {
      const datetime = new Date(datetimeString);
      return {
        datetime,
        layerData: {
          emissions: getTotalEmissionsAvailable(value, mixMode),
        },
        meta: value,
      };
    }
  );

  const totalEmission = chartData[selectedDatetime.index].layerData.emissions;
  // Example usage
  // const emissions = 1000; // Replace with your actual emission value
  // const timeUnit = 'hourly'; // Choose from "hour", "day", "month", or "year"
  const decadeFromStart = selectedFutureDatetime.index;
  const totalTemporaryChangeAllEmissions = calculateTemporaryChange(
    (54 * 10e15) / 8760,
    decadeFromStart,
    Boolean(reduceEmissions)
  );
  const totalTemporaryChange = calculateTemporaryChange(
    totalEmission,
    decadeFromStart,
    Boolean(reduceEmissions)
  );

  console.log(
    `Total temperature change for ${decadeFromStart} years: ${totalTemporaryChange.toFixed(
      2
    )} degrees Celsius`
  );
  return (
    <div className="flex">
      <div>
        <div>
          <animated.div
            style={{
              color: getTextColor(co2ColorScale(intensity)),
              backgroundColor,
            }}
            className="mx-auto flex h-[65px] w-[95px] flex-col items-center justify-center rounded-2xl"
          >
            <p className="select-none text-[1rem]" data-test-id="co2-square-value">
              <span className="font-bold">{totalTemporaryChange.toFixed(4) || '?'}</span>
              &nbsp;
              <span>°C</span>
            </p>
          </animated.div>
        </div>
        <div className="mt-2 flex flex-col items-center">
          <div className="text-center text-sm">
            Change in surface temp from zone electricity consumption
          </div>
          {withSubtext && (
            <div className="text-sm">{CarbonUnits.GRAMS_CO2EQ_PER_WATT_HOUR}</div>
          )}
        </div>
      </div>
      <div>
        <div>
          <animated.div
            style={{
              color: getTextColor(co2ColorScale(intensity)),
              backgroundColor,
            }}
            className="mx-auto flex h-[65px] w-[95px] flex-col items-center justify-center rounded-2xl"
          >
            <p className="select-none text-[1rem]" data-test-id="co2-square-value">
              <span className="font-bold">
                {totalTemporaryChangeAllEmissions.toFixed(4) || '?'}
              </span>
              &nbsp;
              <span>°C</span>
            </p>
          </animated.div>
        </div>
        <div className="mt-2 flex flex-col items-center">
          <div className="text-center text-sm">
            Change in surface temp from all global emissions
          </div>
          {withSubtext && (
            <div className="text-sm">{CarbonUnits.GRAMS_CO2EQ_PER_WATT_HOUR}</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CarbonIntensitySquare;
