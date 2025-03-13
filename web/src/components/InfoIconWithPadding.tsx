import { Info } from 'lucide-react';

/** This component is only meant to be used with `CarbonIntensitySquare` and `CircularGauge`
 * components.
 */
export default function InfoIconWithPadding() {
  return (
    <div className="absolute top-15 rounded-full bg-neutral-100 dark:bg-neutral-900">
      <Info size={28} className="p-1 text-brand-green dark:text-brand-green-dark" />
    </div>
  );
}
