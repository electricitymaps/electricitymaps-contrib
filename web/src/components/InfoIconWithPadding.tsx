import { Info } from 'lucide-react';

/** This component is only meant to be used with `CarbonIntensitySquare` and `CircularGauge`
 * components.
 */
export default function InfoIconWithPadding() {
  return (
    <div className="absolute top-15 rounded-full bg-zinc-50 dark:bg-gray-900">
      <Info size={28} className="p-1 text-brand-green" />
    </div>
  );
}
